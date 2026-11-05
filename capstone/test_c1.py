"""Capstone acceptance tests: the spec in README.md, as executable checks."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from support import target

database = target(__file__, "database")
main = target(__file__, "main")


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    database.Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with TestSession() as s:
            yield s

    main.app.dependency_overrides[database.get_session] = override
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


class Api:
    """Tiny helper so tests read like user stories."""

    def __init__(self, client, email, name):
        self.c = client
        r = client.post("/auth/register", json={"email": email, "name": name, "password": "password123"})
        assert r.status_code == 201, r.text
        self.id = r.json()["id"]
        token = client.post("/auth/token", data={"username": email, "password": "password123"}).json()["access_token"]
        self.h = {"Authorization": f"Bearer {token}"}

    def get(self, url, **kw):
        return self.c.get(url, headers=self.h, **kw)

    def post(self, url, json=None):
        return self.c.post(url, json=json, headers=self.h)

    def patch(self, url, json):
        return self.c.patch(url, json=json, headers=self.h)

    def delete(self, url):
        return self.c.delete(url, headers=self.h)


@pytest.fixture
def team(client):
    ada, bob, eve = Api(client, "ada@example.com", "Ada"), Api(client, "bob@example.com", "Bob"), Api(client, "eve@example.com", "Eve")
    project = ada.post("/projects", {"name": "Launch", "description": "Ship it"}).json()
    assert ada.post(f"/projects/{project['id']}/members", {"email": "bob@example.com"}).status_code == 201
    return ada, bob, eve, project["id"]


# ---- auth ------------------------------------------------------------------------------------
def test_auth_flow(client):
    ada = Api(client, "Ada@Example.com", "Ada")
    assert ada.get("/users/me").json() == {"id": 1, "email": "ada@example.com", "name": "Ada"}
    assert client.get("/users/me").status_code == 401
    assert client.post("/auth/register", json={"email": "ada@example.com", "name": "X", "password": "password123"}).status_code == 409


# ---- projects ----------------------------------------------------------------------------------
def test_create_project(client):
    ada = Api(client, "ada@example.com", "Ada")
    r = ada.post("/projects", {"name": "Launch"})
    assert r.status_code == 201 and r.headers["location"] == f"/projects/{r.json()['id']}"
    body = r.json()
    assert body["owner_id"] == ada.id and body["description"] == ""
    assert [m["email"] for m in body["members"]] == ["ada@example.com"], "the owner is automatically a member"
    assert ada.post("/projects", {"name": ""}).status_code == 422
    assert ada.post("/projects", {"name": "X", "owner_id": 99}).status_code == 422, "no mass assignment"


def test_project_visibility(team):
    ada, bob, eve, pid = team
    eve.post("/projects", {"name": "Eve's secret"})
    assert [p["name"] for p in bob.get("/projects").json()] == ["Launch"]
    assert [p["name"] for p in eve.get("/projects").json()] == ["Eve's secret"]
    assert bob.get(f"/projects/{pid}").status_code == 200
    assert eve.get(f"/projects/{pid}").status_code == 404, "non-members get 404, not 403 (don't leak existence)"


def test_only_owner_manages_project(team):
    ada, bob, eve, pid = team
    assert bob.patch(f"/projects/{pid}", {"name": "Hijacked"}).status_code == 403
    assert ada.patch(f"/projects/{pid}", {"name": "Launch v2"}).json()["name"] == "Launch v2"
    assert bob.post(f"/projects/{pid}/members", {"email": "eve@example.com"}).status_code == 403
    assert bob.delete(f"/projects/{pid}").status_code == 403
    assert eve.delete(f"/projects/{pid}").status_code == 404


def test_membership_rules(team):
    ada, bob, eve, pid = team
    assert ada.post(f"/projects/{pid}/members", {"email": "nobody@example.com"}).status_code == 404
    assert ada.post(f"/projects/{pid}/members", {"email": "bob@example.com"}).status_code == 409
    assert ada.delete(f"/projects/{pid}/members/{ada.id}").status_code == 422, "the owner can't be removed"
    task = ada.post(f"/projects/{pid}/tasks", {"title": "Bob's job", "assignee_id": bob.id}).json()
    assert ada.delete(f"/projects/{pid}/members/{bob.id}").status_code == 204
    assert bob.get(f"/projects/{pid}").status_code == 404
    assert ada.get(f"/tasks/{task['id']}").json()["assignee_id"] is None, "removed members' tasks become unassigned"


def test_delete_project_cascades(team):
    ada, bob, eve, pid = team
    task = ada.post(f"/projects/{pid}/tasks", {"title": "t"}).json()
    assert ada.delete(f"/projects/{pid}").status_code == 204
    assert ada.get(f"/projects/{pid}").status_code == 404
    assert ada.get(f"/tasks/{task['id']}").status_code == 404


# ---- tasks ---------------------------------------------------------------------------------------
def test_create_task_defaults_and_validation(team):
    ada, bob, eve, pid = team
    r = bob.post(f"/projects/{pid}/tasks", {"title": "Write docs", "due_date": "2030-05-01"})
    assert r.status_code == 201 and r.headers["location"] == f"/tasks/{r.json()['id']}"
    t = r.json()
    assert (t["status"], t["priority"], t["assignee_id"], t["created_by_id"], t["completed_at"]) == ("todo", "medium", None, bob.id, None)
    assert t["due_date"] == "2030-05-01" and t["project_id"] == pid
    assert bob.post(f"/projects/{pid}/tasks", {"title": "x", "status": "blocked"}).status_code == 422
    assert bob.post(f"/projects/{pid}/tasks", {"title": "x", "assignee_id": eve.id}).status_code == 422, "assignee must be a member"
    assert eve.post(f"/projects/{pid}/tasks", {"title": "x"}).status_code == 404


def test_task_access(team):
    ada, bob, eve, pid = team
    tid = ada.post(f"/projects/{pid}/tasks", {"title": "t"}).json()["id"]
    assert bob.get(f"/tasks/{tid}").status_code == 200
    assert eve.get(f"/tasks/{tid}").status_code == 404
    assert eve.patch(f"/tasks/{tid}", {"title": "x"}).status_code == 404


def test_update_task_and_completion(team):
    ada, bob, eve, pid = team
    tid = ada.post(f"/projects/{pid}/tasks", {"title": "t"}).json()["id"]
    r = bob.patch(f"/tasks/{tid}", {"status": "done", "assignee_id": bob.id})
    assert r.status_code == 200
    assert r.json()["status"] == "done" and r.json()["completed_at"] is not None and r.json()["title"] == "t"
    reopened = bob.patch(f"/tasks/{tid}", {"status": "in_progress"}).json()
    assert reopened["completed_at"] is None
    assert bob.patch(f"/tasks/{tid}", {"assignee_id": eve.id}).status_code == 422
    assert bob.patch(f"/tasks/{tid}", {"assignee_id": None}).json()["assignee_id"] is None


def test_delete_task_permissions(team):
    ada, bob, eve, pid = team
    by_ada = ada.post(f"/projects/{pid}/tasks", {"title": "a"}).json()["id"]
    by_bob = bob.post(f"/projects/{pid}/tasks", {"title": "b"}).json()["id"]
    assert bob.delete(f"/tasks/{by_ada}").status_code == 403, "members can only delete their own tasks"
    assert bob.delete(f"/tasks/{by_bob}").status_code == 204
    assert ada.delete(f"/tasks/{by_ada}").status_code == 204, "the owner can delete any task"


@pytest.fixture
def seeded(team):
    ada, bob, eve, pid = team
    rows = [
        ("Design schema", "high", "done", ada.id, "2030-01-10"),
        ("Write API", "high", "in_progress", bob.id, "2030-01-05"),
        ("Docs", "low", "todo", bob.id, None),
        ("Deploy", "medium", "todo", None, "2030-02-01"),
        ("Fix login bug", "high", "todo", ada.id, "2030-01-03"),
    ]
    for title, priority, status, assignee, due in rows:
        r = ada.post(f"/projects/{pid}/tasks", {"title": title, "priority": priority, "status": status, "assignee_id": assignee, "due_date": due})
        assert r.status_code == 201, r.text
    return team


def titles(r):
    assert r.status_code == 200, r.text
    return [t["title"] for t in r.json()["items"]]


def test_list_filters_and_envelope(seeded):
    ada, bob, eve, pid = seeded
    url = f"/projects/{pid}/tasks"
    page = ada.get(url, params={"limit": 2}).json()
    assert page["total"] == 5 and page["limit"] == 2 and page["offset"] == 0 and len(page["items"]) == 2
    assert titles(ada.get(url, params={"status": "todo"})) == ["Docs", "Deploy", "Fix login bug"]
    assert titles(ada.get(url, params={"assignee_id": bob.id})) == ["Write API", "Docs"]
    assert titles(ada.get(url, params={"priority": "high", "status": "todo"})) == ["Fix login bug"]
    r = ada.get(url, params={"q": "API"})
    assert titles(r) == ["Write API"] and r.json()["total"] == 1
    assert eve.get(url).status_code == 404


def test_list_sorting(seeded):
    ada, bob, eve, pid = seeded
    url = f"/projects/{pid}/tasks"
    assert titles(ada.get(url, params={"sort": "due_date"})) == ["Fix login bug", "Write API", "Design schema", "Deploy", "Docs"]
    assert titles(ada.get(url, params={"sort": "-priority,title"})) == ["Design schema", "Fix login bug", "Write API", "Deploy", "Docs"]
    assert ada.get(url, params={"sort": "assignee_id; DROP TABLE tasks"}).status_code == 422


def test_my_tasks(seeded):
    ada, bob, eve, pid = seeded
    assert titles(bob.get("/me/tasks")) == ["Write API", "Docs"]
    assert titles(bob.get("/me/tasks", params={"status": "todo"})) == ["Docs"]
    assert eve.get("/me/tasks").json()["total"] == 0

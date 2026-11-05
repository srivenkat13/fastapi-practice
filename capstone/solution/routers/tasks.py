from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import asc, case, desc, func, or_, select

from ..access import get_project_for_member, get_task_for_member, validate_assignee
from ..deps import DB, CurrentUser
from ..models import Task
from ..schemas import Page, Priority, Status, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(tags=["tasks"])

PRIORITY_RANK = case({"low": 1, "medium": 2, "high": 3}, value=Task.priority)
SORTABLE = {"due_date": Task.due_date, "priority": PRIORITY_RANK, "created_at": Task.created_at, "title": Task.title}


def parse_sort(sort: str) -> list:
    clauses = []
    for part in filter(None, (p.strip() for p in sort.split(","))):
        direction, field = (desc, part[1:]) if part.startswith("-") else (asc, part)
        if field not in SORTABLE:
            raise HTTPException(422, f"Cannot sort by '{field}'")
        column = SORTABLE[field]
        # NULL due dates last regardless of direction
        clauses.append(direction(column).nulls_last() if field == "due_date" else direction(column))
    return clauses


def paginate(db: DB, stmt, sort: str, limit: int, offset: int) -> dict:
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(*parse_sort(sort), Task.id).limit(limit).offset(offset)).all()
    return {"items": rows, "total": total, "limit": limit, "offset": offset}


Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(project_id: int, data: TaskCreate, user: CurrentUser, db: DB, response: Response):
    project = get_project_for_member(db, project_id, user)
    validate_assignee(project, data.assignee_id)
    task = Task(**data.model_dump(), project_id=project.id, created_by_id=user.id)
    if task.status == Status.done:
        task.completed_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()
    response.headers["Location"] = f"/tasks/{task.id}"
    return task


@router.get("/projects/{project_id}/tasks", response_model=Page[TaskOut])
def list_tasks(
    project_id: int,
    user: CurrentUser,
    db: DB,
    status: Status | None = None,
    priority: Priority | None = None,
    assignee_id: int | None = None,
    q: Annotated[str | None, Query(min_length=1)] = None,
    sort: str = "created_at",
    limit: Limit = 20,
    offset: Offset = 0,
):
    get_project_for_member(db, project_id, user)
    stmt = select(Task).where(Task.project_id == project_id)
    if status:
        stmt = stmt.where(Task.status == status.value)
    if priority:
        stmt = stmt.where(Task.priority == priority.value)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if q:
        stmt = stmt.where(or_(Task.title.ilike(f"%{q}%"), Task.description.ilike(f"%{q}%")))
    return paginate(db, stmt, sort, limit, offset)


@router.get("/me/tasks", response_model=Page[TaskOut])
def my_tasks(user: CurrentUser, db: DB, status: Status | None = None, sort: str = "due_date", limit: Limit = 20, offset: Offset = 0):
    stmt = select(Task).where(Task.assignee_id == user.id)
    if status:
        stmt = stmt.where(Task.status == status.value)
    return paginate(db, stmt, sort, limit, offset)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, user: CurrentUser, db: DB):
    return get_task_for_member(db, task_id, user)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, user: CurrentUser, db: DB):
    task = get_task_for_member(db, task_id, user)
    changes = data.model_dump(exclude_unset=True)
    if "assignee_id" in changes:
        validate_assignee(task.project, changes["assignee_id"])
    if "status" in changes and changes["status"] != task.status:
        task.completed_at = datetime.now(timezone.utc) if changes["status"] == Status.done else None
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    return task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user: CurrentUser, db: DB) -> None:
    task = get_task_for_member(db, task_id, user)
    if user.id not in (task.created_by_id, task.project.owner_id):
        raise HTTPException(403, "Only the task creator or project owner can delete it")
    db.delete(task)
    db.commit()

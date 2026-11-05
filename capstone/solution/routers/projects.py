from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..access import get_project_for_member, require_owner
from ..deps import DB, CurrentUser
from ..models import Project, Task, User, project_members
from ..schemas import AddMember, ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(data: ProjectCreate, user: CurrentUser, db: DB, response: Response):
    project = Project(**data.model_dump(), owner_id=user.id, members=[user])
    db.add(project)
    db.commit()
    response.headers["Location"] = f"/projects/{project.id}"
    return project


@router.get("", response_model=list[ProjectOut])
def my_projects(user: CurrentUser, db: DB):
    stmt = (
        select(Project)
        .join(project_members, project_members.c.project_id == Project.id)
        .where(project_members.c.user_id == user.id)
        .options(selectinload(Project.members))
        .order_by(Project.id)
    )
    return db.scalars(stmt).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, user: CurrentUser, db: DB):
    return get_project_for_member(db, project_id, user)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectUpdate, user: CurrentUser, db: DB):
    project = get_project_for_member(db, project_id, user)
    require_owner(project, user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, user: CurrentUser, db: DB) -> None:
    project = get_project_for_member(db, project_id, user)
    require_owner(project, user)
    db.delete(project)
    db.commit()


@router.post("/{project_id}/members", response_model=ProjectOut, status_code=201)
def add_member(project_id: int, data: AddMember, user: CurrentUser, db: DB):
    project = get_project_for_member(db, project_id, user)
    require_owner(project, user)
    new_member = db.scalar(select(User).where(User.email == data.email.lower()))
    if new_member is None:
        raise HTTPException(404, "User not found")
    if new_member in project.members:
        raise HTTPException(409, "Already a member")
    project.members.append(new_member)
    db.commit()
    return project


@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(project_id: int, user_id: int, user: CurrentUser, db: DB) -> None:
    project = get_project_for_member(db, project_id, user)
    require_owner(project, user)
    if user_id == project.owner_id:
        raise HTTPException(422, "The owner cannot be removed")
    member = next((m for m in project.members if m.id == user_id), None)
    if member is None:
        raise HTTPException(404, "Not a member")
    project.members.remove(member)
    # Their tasks in THIS project become unassigned (one UPDATE, not a loop).
    db.execute(update(Task).where(Task.project_id == project.id, Task.assignee_id == user_id).values(assignee_id=None))
    db.commit()

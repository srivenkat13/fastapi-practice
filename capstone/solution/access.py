"""Authorization helpers: every rule about "who may touch what" lives here, in one place."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import Project, Task, User


def get_project_for_member(db: Session, project_id: int, user: User) -> Project:
    """404 (not 403) for non-members: don't reveal that the project exists."""
    project = db.get(Project, project_id)
    if project is None or user not in project.members:
        raise HTTPException(404, "Project not found")
    return project


def require_owner(project: Project, user: User) -> None:
    if project.owner_id != user.id:
        raise HTTPException(403, "Only the project owner can do that")


def get_task_for_member(db: Session, task_id: int, user: User) -> Task:
    task = db.get(Task, task_id)
    if task is None or user not in task.project.members:
        raise HTTPException(404, "Task not found")
    return task


def validate_assignee(project: Project, assignee_id: int | None) -> None:
    if assignee_id is not None and assignee_id not in {m.id for m in project.members}:
        raise HTTPException(422, "Assignee must be a member of the project")

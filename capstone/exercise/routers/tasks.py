"""TODO: implement the task endpoints from the README spec:
POST/GET /projects/{id}/tasks, GET/PATCH/DELETE /tasks/{id}, GET /me/tasks."""
from fastapi import APIRouter

router = APIRouter(tags=["tasks"])

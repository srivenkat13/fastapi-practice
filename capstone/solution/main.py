from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import Base, engine
from .routers import auth, projects, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Task Tracker API", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

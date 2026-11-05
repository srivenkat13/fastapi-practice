"""⏱ 25 minutes. This notes API has 7 bugs. The tests describe correct behaviour; fix the code, not the tests.
Narrate as you go: "the test expects X, we return Y, because..."
"""
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="D3 · Fix the bugs")
NOTES: dict[int, dict] = {}


class NoteIn(BaseModel):
    title: str = Field(min_length=1)
    body: str = ""
    tags: list[str] = []


class NotePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    body: str | None = None
    tags: list[str] | None = None


class NoteOut(BaseModel):
    id: int
    title: str
    body: str
    tags: list[str]


def normalise_tags(tags, seen=[]):
    for t in tags:
        t = t.strip().lower()
        if t not in seen:
            seen.append(t)
    return seen


def owner(x_token: Annotated[str | None, Header()] = None) -> str:
    if not x_token:
        raise HTTPException(401, "Missing X-Token")
    return x_token


@app.post("/notes")
def create_note(data: NoteIn, x_token: Annotated[str | None, Header()] = None):
    token = owner(x_token)
    note_id = len(NOTES) + 1
    NOTES[note_id] = {"id": note_id, "title": data.title, "body": data.body, "tags": normalise_tags(data.tags), "owner_token": token}
    return NOTES[note_id]


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int):
    if note_id not in NOTES:
        raise HTTPException(404, "Note not found")
    return NOTES[note_id]


@app.get("/notes/stats")
def stats():
    return {"count": len(NOTES), "tags": sorted({t for n in NOTES.values() for t in n["tags"]})}


@app.get("/notes", response_model=list[NoteOut])
def list_notes(q: str | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 10, offset: Annotated[int, Query(ge=0)] = 0):
    notes = list(NOTES.values())
    if q:
        notes = [n for n in notes if q in n["title"]]
    return notes[offset : offset + limit - 1]


@app.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NotePatch):
    if note_id not in NOTES:
        raise HTTPException(404, "Note not found")
    NOTES[note_id].update(data.model_dump())
    return NOTES[note_id]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    NOTES.pop(note_id, None)
    return {"deleted": True}

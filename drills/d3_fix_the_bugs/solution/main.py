"""D3 solution. Each fix is labelled with the bug it addresses."""
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Header, Query, Response
from pydantic import BaseModel, Field

app = FastAPI(title="D3 · Fix the bugs")
NOTES: dict[int, dict] = {}


class NoteIn(BaseModel):
    title: str = Field(min_length=1)
    body: str = ""
    tags: list[str] = []  # fine: Pydantic copies field defaults per instance (unlike function defaults)


class NotePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    body: str | None = None
    tags: list[str] | None = None


class NoteOut(BaseModel):
    id: int
    title: str
    body: str
    tags: list[str]


# BUG 1: mutable default argument → tags leaked between notes. Use a fresh list per call.
def normalise_tags(tags: list[str]) -> list[str]:
    seen: list[str] = []
    for t in tags:
        t = t.strip().lower()
        if t not in seen:
            seen.append(t)
    return seen


def owner(x_token: Annotated[str | None, Header()] = None) -> str:
    if not x_token:
        raise HTTPException(401, "Missing X-Token")
    return x_token


# BUG 2: 200 → 201 for creation.  BUG 3: response leaked owner_token → response_model=NoteOut.
@app.post("/notes", response_model=NoteOut, status_code=201)
def create_note(data: NoteIn, token: Annotated[str, Depends(owner)]):
    note_id = max(NOTES, default=0) + 1  # (bonus: len()+1 reuses ids after a delete)
    NOTES[note_id] = {"id": note_id, "title": data.title, "body": data.body, "tags": normalise_tags(data.tags), "owner_token": token}
    return NOTES[note_id]


# BUG 4: route order. /notes/stats must be declared before /notes/{note_id}.
@app.get("/notes/stats")
def stats():
    return {"count": len(NOTES), "tags": sorted({t for n in NOTES.values() for t in n["tags"]})}


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int):
    if note_id not in NOTES:
        raise HTTPException(404, "Note not found")
    return NOTES[note_id]


@app.get("/notes", response_model=list[NoteOut])
def list_notes(q: str | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 10, offset: Annotated[int, Query(ge=0)] = 0):
    notes = list(NOTES.values())
    if q:
        notes = [n for n in notes if q.lower() in n["title"].lower()]  # BUG 5: search was case-sensitive
    return notes[offset : offset + limit]  # BUG 6: off-by-one (limit - 1)


@app.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NotePatch):
    if note_id not in NOTES:
        raise HTTPException(404, "Note not found")
    changes = data.model_dump(exclude_unset=True)  # BUG 7: unset fields overwrote data with None
    if "tags" in changes:
        changes["tags"] = normalise_tags(changes["tags"])
    NOTES[note_id].update(changes)
    return NOTES[note_id]


# (also BUG 2) DELETE → 204 with no body, and 404 for a missing note
@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> Response:
    if NOTES.pop(note_id, None) is None:
        raise HTTPException(404, "Note not found")
    return Response(status_code=204)

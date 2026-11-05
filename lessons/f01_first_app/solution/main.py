from fastapi import FastAPI

app = FastAPI(title="Bookshelf API", version="0.1.0")

BOOKS = [
    {"id": 1, "title": "Fluent Python", "author": "Luciano Ramalho"},
    {"id": 2, "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann"},
    {"id": 3, "title": "Clean Architecture", "author": "Robert C. Martin"},
]


@app.get("/")
def root():
    return {"message": "Welcome to the Bookshelf API. See /docs"}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@app.get("/books", tags=["books"], summary="List all books")
def list_books():
    return BOOKS

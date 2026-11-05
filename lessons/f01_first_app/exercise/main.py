from fastapi import FastAPI

# TODO 1: title "Bookshelf API", version "0.1.0"
app = FastAPI()

BOOKS = [
    {"id": 1, "title": "Fluent Python", "author": "Luciano Ramalho"},
    {"id": 2, "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann"},
    {"id": 3, "title": "Clean Architecture", "author": "Robert C. Martin"},
]


@app.get("/")
def root():
    return {"message": "Welcome to the Bookshelf API. See /docs"}


# TODO 2: GET /health -> {"status": "ok"}, tag "meta"

# TODO 3: GET /books -> BOOKS, tag "books", summary "List all books"

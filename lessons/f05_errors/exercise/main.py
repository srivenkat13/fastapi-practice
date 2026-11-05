from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request  # noqa: F401
from fastapi.exceptions import RequestValidationError  # noqa: F401
from fastapi.responses import JSONResponse  # noqa: F401
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: F401

app = FastAPI(title="F05 · Errors")

STOCK = {1: 3, 2: 0}
TITLES = {1: "Fluent Python", 2: "Dune"}


# TODO: AppError(Exception) with status_code / code class attributes and a .message
#       NotFound(AppError): 404 "not_found"      OutOfStock(AppError): 409 "out_of_stock"


# ---- service layer (no HTTP here!) ------------------------------------------
def get_book(book_id: int) -> dict:
    if book_id not in TITLES:
        raise HTTPException(404, "nope")  # TODO: raise NotFound(f"Book {book_id} not found")
    return {"id": book_id, "title": TITLES[book_id], "stock": STOCK[book_id]}


def reserve(book_id: int, quantity: int) -> dict:
    book = get_book(book_id)
    if book["stock"] < quantity:
        raise HTTPException(409, "no stock")  # TODO: raise OutOfStock(f"Book {book_id} is out of stock")
    STOCK[book_id] -= quantity
    return {"book_id": book_id, "reserved": quantity, "remaining": STOCK[book_id]}


# ---- HTTP layer ---------------------------------------------------------------
@app.get("/books/{book_id}")
def read_book(book_id: int):
    return get_book(book_id)


@app.post("/books/{book_id}/reserve")
def reserve_book(book_id: int, quantity: Annotated[int, Query(gt=0)] = 1):
    return reserve(book_id, quantity)


@app.get("/boom")
def boom():
    raise RuntimeError("database password is hunter2")  # must never reach the client


# TODO: exception handlers producing {"error": {"code": ..., "message": ..., "details": [...]}}
#   AppError                -> exc.status_code, exc.code, exc.message, details []
#   RequestValidationError  -> 422, "validation_error", "Invalid request", details [{"field": "query.quantity", "message": ...}]
#                              (field = loc joined with ".", e.g. ("query", "quantity") -> "query.quantity")
#   StarletteHTTPException  -> exc.status_code, f"http_{exc.status_code}", str(exc.detail), []
#   Exception               -> 500, "internal_error", "Something went wrong", []

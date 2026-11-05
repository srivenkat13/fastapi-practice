import logging
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("bookstore")
app = FastAPI(title="F05 · Errors")

STOCK = {1: 3, 2: 0}
TITLES = {1: "Fluent Python", 2: "Dune"}


class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFound(AppError):
    status_code, code = 404, "not_found"


class OutOfStock(AppError):
    status_code, code = 409, "out_of_stock"


# ---- service layer (no HTTP here!) ------------------------------------------
def get_book(book_id: int) -> dict:
    if book_id not in TITLES:
        raise NotFound(f"Book {book_id} not found")
    return {"id": book_id, "title": TITLES[book_id], "stock": STOCK[book_id]}


def reserve(book_id: int, quantity: int) -> dict:
    book = get_book(book_id)
    if book["stock"] < quantity:
        raise OutOfStock(f"Book {book_id} is out of stock")
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
    raise RuntimeError("database password is hunter2")


def error_response(status: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or []}})


@app.exception_handler(AppError)
async def on_app_error(request: Request, exc: AppError):
    return error_response(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def on_validation_error(request: Request, exc: RequestValidationError):
    details = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return error_response(422, "validation_error", "Invalid request", details)


@app.exception_handler(StarletteHTTPException)
async def on_http_error(request: Request, exc: StarletteHTTPException):
    return error_response(exc.status_code, f"http_{exc.status_code}", str(exc.detail))


@app.exception_handler(Exception)
async def on_unhandled(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response(500, "internal_error", "Something went wrong")

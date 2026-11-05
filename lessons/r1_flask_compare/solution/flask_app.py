"""The same API in Flask, using an app factory, a blueprint, hand-written validation and g/current_app."""
import copy
import uuid

from flask import Blueprint, Flask, current_app, g, jsonify, request

SEED = [
    {"id": 1, "title": "Fluent Python", "genre": "tech", "year": 2022},
    {"id": 2, "title": "Dune", "genre": "fiction", "year": 1965},
]

books_bp = Blueprint("books", __name__)


def books() -> list[dict]:
    return current_app.extensions["books"]  # per-app storage (no module globals shared between apps)


def validate(data) -> tuple[dict, dict]:
    """What Pydantic does for free in FastAPI, written by hand."""
    if not isinstance(data, dict):
        return {}, {"body": "Expected a JSON object"}
    errors, clean = {}, {}
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        errors["title"] = "Title is required"
    else:
        clean["title"] = title
    year = data.get("year")
    if not isinstance(year, int) or isinstance(year, bool) or not 1450 <= year <= 2100:
        errors["year"] = "Year must be an integer between 1450 and 2100"
    else:
        clean["year"] = year
    genre = data.get("genre", "tech")
    if not isinstance(genre, str):
        errors["genre"] = "Genre must be a string"
    else:
        clean["genre"] = genre
    return clean, errors


@books_bp.get("")
def list_books():
    genre = request.args.get("genre")
    return jsonify([b for b in books() if genre is None or b["genre"] == genre])


@books_bp.get("/<int:book_id>")  # the int converter: /books/abc simply doesn't match → 404
def get_book(book_id: int):
    for b in books():
        if b["id"] == book_id:
            return b
    return {"detail": "Book not found"}, 404


@books_bp.post("")
def create_book():
    if request.headers.get("X-API-Key") != current_app.config["API_KEY"]:
        return {"detail": "Invalid API key"}, 401
    clean, errors = validate(request.get_json(silent=True))
    if errors:
        return {"detail": errors}, 422
    book = {"id": len(books()) + 1, "genre": clean["genre"], "title": clean["title"], "year": clean["year"]}
    books().append(book)
    return book, 201


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update({"API_KEY": "letmein", **(config or {})})
    app.extensions["books"] = copy.deepcopy(SEED)
    app.register_blueprint(books_bp, url_prefix="/books")

    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

    @app.after_request
    def add_request_id(response):
        response.headers["X-Request-ID"] = g.request_id
        return response

    @app.errorhandler(404)
    def not_found(_error):
        return {"detail": "Not Found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return {"detail": "Method Not Allowed"}, 405

    return app

"""Rebuild ../fastapi_app.py in Flask. Run: flask --app lessons.r1_flask_compare.exercise.flask_app:create_app run --port 5001

Requirements (the tests check each):
  - an app factory create_app(config: dict | None = None) -> Flask, with config["API_KEY"] defaulting to "letmein"
  - a Blueprint "books" registered at url_prefix "/books"
  - GET  /books?genre=...           -> JSON list (filtered)
  - GET  /books/<int:book_id>       -> JSON book | 404 {"detail": "Book not found"}
  - POST /books                     -> 201 JSON book; X-API-Key must equal config API_KEY (else 401 {"detail": ...});
                                       validate by hand: title non-empty str, year int 1450..2100, genre optional str
                                       (default "tech"); invalid/missing JSON -> 422 {"detail": {"<field>": "<message>"}}
  - unknown routes -> JSON 404 {"detail": "Not Found"} (an errorhandler, not Flask's HTML page)
  - before_request/after_request: echo or generate X-Request-ID on every response (store it on flask.g)
  - each app instance has its OWN books list (copy SEED in the factory), so tests don't leak state
"""
import copy  # noqa: F401
import uuid  # noqa: F401

from flask import Blueprint, Flask, current_app, g, jsonify, request  # noqa: F401

SEED = [
    {"id": 1, "title": "Fluent Python", "genre": "tech", "year": 2022},
    {"id": 2, "title": "Dune", "genre": "fiction", "year": 1965},
]


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return {"message": "TODO: rebuild the books API"}

    return app

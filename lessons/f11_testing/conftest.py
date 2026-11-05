"""Fixtures for YOUR tests in exercise/tests_cart_api.py. (Shared with the solution.)

The grader sets F11_BUGS to build mutant apps. You never need to touch that; just use
the `app` and `client` fixtures.
"""
import os

import pytest
from fastapi.testclient import TestClient

from lessons.f11_testing.cartapp.app import create_app


@pytest.fixture
def app():
    bugs = frozenset(b for b in os.environ.get("F11_BUGS", "").split(",") if b)
    return create_app(bugs)  # a fresh app (and fresh in-memory carts) for every test


@pytest.fixture
def client(app):
    return TestClient(app)

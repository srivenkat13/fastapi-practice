import json
from pathlib import Path  # noqa: F401

from .models import Product

# 🐛 A relative *filesystem* path is resolved against the current working directory,
# not this file. It breaks as soon as you run from anywhere else.
# Fix: build it from this module's location with pathlib: Path(__file__).parent / "products.json"
DATA_FILE = "products.json"


def load_products(path=None) -> list[Product]:
    """Read the JSON file (default DATA_FILE) and return Product objects."""
    with open(path or DATA_FILE) as f:
        return [Product(**row) for row in json.load(f)]


# TODO: add a `if __name__ == "__main__":` block that prints each product name.
# Run it with:  python -m lessons.p5_modules.exercise.storage   (from the repo root)

import json
from pathlib import Path

from .models import Product

DATA_FILE = Path(__file__).parent / "products.json"


def load_products(path: Path | str | None = None) -> list[Product]:
    data = json.loads(Path(path or DATA_FILE).read_text())
    return [Product(**row) for row in data]


if __name__ == "__main__":  # runs only via `python -m ...storage`, never on import
    for product in load_products():
        print(product.name)

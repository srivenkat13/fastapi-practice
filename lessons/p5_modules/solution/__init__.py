"""The package's public API."""
from .inventory import Inventory
from .models import Product
from .storage import load_products

__all__ = ["Product", "Inventory", "load_products"]


def build_inventory() -> Inventory:
    return Inventory(load_products())

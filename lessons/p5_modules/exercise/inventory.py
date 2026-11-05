from models import Product  # 🐛 absolute import of a sibling: only works if you `cd` into this folder


class Inventory:
    def __init__(self, products: list[Product]):
        self._by_sku = {p.sku: p for p in products}

    def get(self, sku: str) -> Product | None:
        return self._by_sku.get(sku)

    def available(self) -> list[Product]:
        return [p for p in self._by_sku.values() if p.in_stock]

    def total_value_cents(self) -> int:
        return sum(p.price_cents * p.stock for p in self._by_sku.values())

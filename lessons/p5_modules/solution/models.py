from dataclasses import dataclass


@dataclass
class Product:
    sku: str
    name: str
    price_cents: int
    stock: int = 0

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

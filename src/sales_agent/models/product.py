from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ProductVariant(BaseModel):
    id: int
    title: str
    price: Decimal
    sku: str | None = None
    inventory_quantity: int = 0


class Product(BaseModel):
    id: int
    title: str
    product_type: str | None = None
    vendor: str | None = None
    status: str
    variants: list[ProductVariant] = []
    created_at: datetime
    updated_at: datetime

    @property
    def min_price(self) -> Decimal | None:
        if not self.variants:
            return None
        return min(v.price for v in self.variants)

    @property
    def total_inventory(self) -> int:
        return sum(v.inventory_quantity for v in self.variants)


class ProductsResponse(BaseModel):
    products: list[Product]

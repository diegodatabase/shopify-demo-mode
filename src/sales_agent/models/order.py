from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ShippingAddress(BaseModel):
    city: str | None = None
    province: str | None = None
    province_code: str | None = None
    country: str | None = None
    country_code: str | None = None


class LineItem(BaseModel):
    id: int
    product_id: int | None = None
    variant_id: int | None = None
    title: str
    quantity: int
    price: Decimal
    sku: str | None = None
    product_type: str | None = None
    vendor: str | None = None

    @property
    def total(self) -> Decimal:
        return self.price * self.quantity


class Order(BaseModel):
    id: int
    order_number: int
    created_at: datetime
    currency: str
    total_price: Decimal
    subtotal_price: Decimal
    financial_status: str
    fulfillment_status: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    shipping_address: ShippingAddress | None = None

    @property
    def state(self) -> str | None:
        """Retorna o province_code (UF) do endereço de entrega."""
        if self.shipping_address:
            return self.shipping_address.province_code
        return None


class OrdersResponse(BaseModel):
    orders: list[Order]

"""
ORM models SQLAlchemy 2.

Separados dos Pydantic models de `sales_agent.models` — estes representam
as tabelas do banco, aqueles representam o contrato com a API Shopify.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # ID Shopify
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    financial_status: Mapped[str] = mapped_column(String(50), nullable=False)
    fulfillment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Endereço de entrega (desnormalizado para simplificar queries analíticas)
    shipping_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(10), nullable=True)   # province_code (UF)
    shipping_country_code: Mapped[str | None] = mapped_column(String(5), nullable=True)

    line_items: Mapped[list["LineItemORM"]] = relationship(
        "LineItemORM", back_populates="order", cascade="all, delete-orphan"
    )


class LineItemORM(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # ID Shopify
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(200), nullable=True)

    order: Mapped["OrderORM"] = relationship("OrderORM", back_populates="line_items")

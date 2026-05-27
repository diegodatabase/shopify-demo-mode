"""
OrderRepository: camada de acesso a dados para pedidos.

Isola as queries SQLAlchemy do restante da aplicação.
Tools e agents nunca tocam o ORM diretamente.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from sales_agent.db.models import LineItemORM, OrderORM
from sales_agent.models.order import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_orders(self, orders: list[Order]) -> int:
        """
        Insere ou atualiza pedidos (upsert por ID Shopify).
        Retorna o número de pedidos processados.
        """
        existing_ids = set(
            self._session.scalars(
                select(OrderORM.id).where(
                    OrderORM.id.in_([o.id for o in orders])
                )
            ).all()
        )

        count = 0
        for order in orders:
            shipping = order.shipping_address

            if order.id in existing_ids:
                orm = self._session.get(OrderORM, order.id)
                if orm is None:
                    continue
                # Atualiza campos mutáveis (status pode mudar)
                orm.financial_status = order.financial_status
                orm.fulfillment_status = order.fulfillment_status
                orm.total_price = order.total_price
                orm.subtotal_price = order.subtotal_price
            else:
                orm = OrderORM(
                    id=order.id,
                    order_number=order.order_number,
                    created_at=order.created_at,
                    currency=order.currency,
                    total_price=order.total_price,
                    subtotal_price=order.subtotal_price,
                    financial_status=order.financial_status,
                    fulfillment_status=order.fulfillment_status,
                    shipping_city=shipping.city if shipping else None,
                    shipping_state=shipping.province_code if shipping else None,
                    shipping_country_code=shipping.country_code if shipping else None,
                )
                self._session.add(orm)

                for item in order.line_items:
                    self._session.add(LineItemORM(
                        id=item.id,
                        order_id=order.id,
                        product_id=item.product_id,
                        title=item.title,
                        quantity=item.quantity,
                        unit_price=item.price,
                        sku=item.sku,
                        product_type=item.product_type,
                        vendor=item.vendor,
                    ))

            count += 1

        return count

    def find_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        financial_status: str = "paid",
    ) -> list[OrderORM]:
        """Retorna pedidos dentro de um período com line_items carregados."""
        stmt = (
            select(OrderORM)
            .where(
                OrderORM.created_at >= start_date,
                OrderORM.created_at <= end_date,
            )
            .order_by(OrderORM.created_at)
        )

        if financial_status != "any":
            stmt = stmt.where(OrderORM.financial_status == financial_status)

        return list(self._session.scalars(stmt).unique().all())

    def count(self) -> int:
        return self._session.query(OrderORM).count()

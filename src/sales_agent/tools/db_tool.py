"""
Tools para persistir e recuperar pedidos do PostgreSQL.

save_orders_to_db: chamada após fetch_orders para persistir os dados
load_orders_from_db: alternativa ao fetch_orders quando os dados já estão no banco
"""

import json
from datetime import datetime, timezone

from crewai.tools import tool

from sales_agent.db.models import LineItemORM, OrderORM
from sales_agent.db.repository import OrderRepository
from sales_agent.db.session import get_session
from sales_agent.models.order import Order


def _orm_to_dict(order: OrderORM) -> dict:
    """Converte OrderORM para o mesmo formato JSON que fetch_orders retorna."""
    return {
        "id": order.id,
        "order_number": order.order_number,
        "created_at": order.created_at.isoformat(),
        "currency": order.currency,
        "total_price": str(order.total_price),
        "subtotal_price": str(order.subtotal_price),
        "financial_status": order.financial_status,
        "fulfillment_status": order.fulfillment_status,
        "shipping_address": {
            "city": order.shipping_city,
            "province_code": order.shipping_state,
            "country_code": order.shipping_country_code,
        } if order.shipping_state else None,
        "line_items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "title": item.title,
                "quantity": item.quantity,
                "price": str(item.unit_price),
                "sku": item.sku,
                "product_type": item.product_type,
                "vendor": item.vendor,
            }
            for item in order.line_items
        ],
    }


@tool("save_orders_to_db")
def save_orders_to_db(orders_json: str) -> str:
    """
    Persiste pedidos no PostgreSQL. Faz upsert — pedidos já existentes são atualizados.

    Args:
        orders_json: JSON serializado com lista de pedidos (saída do fetch_orders).

    Returns:
        Mensagem com o número de pedidos salvos.
    """
    raw = json.loads(orders_json)
    if not raw:
        return "Nenhum pedido para salvar."

    orders = [Order.model_validate(o) for o in raw]

    with get_session() as session:
        repo = OrderRepository(session)
        count = repo.upsert_orders(orders)

    return f"{count} pedido(s) salvos/atualizados no banco de dados."


@tool("load_orders_from_db")
def load_orders_from_db(start_date: str, end_date: str, status: str = "paid") -> str:
    """
    Recupera pedidos do PostgreSQL. Use quando os dados já foram sincronizados.

    Args:
        start_date: Data inicial no formato YYYY-MM-DD.
        end_date: Data final no formato YYYY-MM-DD.
        status: Status financeiro. Use 'any' para todos. Padrão: 'paid'.

    Returns:
        JSON serializado com lista de pedidos (mesmo formato do fetch_orders).
    """
    start = datetime.fromisoformat(f"{start_date}T00:00:00").replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(f"{end_date}T23:59:59").replace(tzinfo=timezone.utc)

    with get_session() as session:
        repo = OrderRepository(session)
        orders = repo.find_by_period(start, end, financial_status=status)
        result = [_orm_to_dict(o) for o in orders]

    return json.dumps(result)

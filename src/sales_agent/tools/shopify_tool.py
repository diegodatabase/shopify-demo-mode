"""
Tools para buscar dados da Shopify Admin REST API.

Quando SHOPIFY_DEMO_MODE=true nas settings, retorna dados fictícios gerados
localmente em vez de chamar a API real. Útil para desenvolvimento sem loja.

Paginação via cursor (page_info) — padrão atual da Shopify para evitar
timeout em lojas com muitos pedidos.
"""

import json
from datetime import date, datetime, timedelta, timezone

import httpx
from crewai.tools import tool

from sales_agent.config.settings import get_settings
from sales_agent.models.order import Order, OrdersResponse
from sales_agent.models.product import Product, ProductsResponse


def _is_demo() -> bool:
    return get_settings().shopify_demo_mode


def _headers() -> dict[str, str]:
    return {
        "X-Shopify-Access-Token": get_settings().shopify.access_token,
        "Content-Type": "application/json",
    }


def _fetch_all_orders(client: httpx.Client, params: dict) -> list[Order]:
    """Busca todos os pedidos paginando via cursor."""
    orders: list[Order] = []
    url = f"{get_settings().shopify.base_url}/orders.json"
    current_params: dict | None = params

    while True:
        response = client.get(url, params=current_params, headers=_headers())
        response.raise_for_status()
        batch = OrdersResponse.model_validate(response.json())
        orders.extend(batch.orders)

        link_header = response.headers.get("Link", "")
        next_url = _parse_next_link(link_header)
        if not next_url:
            break
        url = next_url
        current_params = None  # page_info está na next_url; params=None preserva a query string

    return orders


def _parse_next_link(link_header: str) -> str | None:
    """Extrai a URL 'next' do header Link da Shopify."""
    for part in link_header.split(","):
        if 'rel="next"' in part:
            return part.split(";")[0].strip().strip("<>")
    return None


@tool("fetch_orders")
def fetch_orders(start_date: str, end_date: str, status: str = "any") -> str:
    """
    Busca pedidos dentro de um intervalo de datas.
    Em modo demo, retorna dados fictícios sem chamar a API Shopify.

    Args:
        start_date: Data inicial no formato YYYY-MM-DD.
        end_date: Data final no formato YYYY-MM-DD.
        status: Status financeiro. Use 'any' para todos. Padrão: 'any'.

    Returns:
        JSON serializado com lista de pedidos.
    """
    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        start = date.today() - timedelta(days=30)

    try:
        end = date.fromisoformat(end_date)
    except ValueError:
        end = date.today()

    if _is_demo():
        from sales_agent.tools.demo_data import gerar_pedidos
        start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
        end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc)
        pedidos = gerar_pedidos(start_dt, end_dt)
        if status != "any":
            pedidos = [p for p in pedidos if p["financial_status"] == status]
        return json.dumps(pedidos)

    params = {
        "created_at_min": f"{start}T00:00:00-03:00",
        "created_at_max": f"{end}T23:59:59-03:00",
        "financial_status": status,
        "status": "any",
        "limit": 250,
        "fields": (
            "id,order_number,created_at,currency,total_price,"
            "subtotal_price,financial_status,fulfillment_status,"
            "line_items,shipping_address"
        ),
    }

    with httpx.Client(timeout=30.0) as client:
        orders = _fetch_all_orders(client, params)

    return json.dumps([o.model_dump(mode="json") for o in orders])


@tool("fetch_products")
def fetch_products() -> str:
    """
    Busca todos os produtos ativos da loja.
    Em modo demo, retorna catálogo fictício sem chamar a API Shopify.

    Returns:
        JSON serializado com lista de produtos.
    """
    if _is_demo():
        from sales_agent.tools.demo_data import PRODUTOS
        from datetime import datetime
        now = datetime.now(timezone.utc).isoformat()
        produtos = [
            {
                "id": 1000 + i,
                "title": p["title"],
                "product_type": p["product_type"],
                "vendor": p["vendor"],
                "status": "active",
                "created_at": now,
                "updated_at": now,
                "variants": [
                    {
                        "id": (1000 + i) * 10,
                        "title": "Único",
                        "price": str(p["price"]),
                        "sku": f"SKU-{i+1:03d}",
                        "inventory_quantity": 50,
                    }
                ],
            }
            for i, p in enumerate(PRODUTOS)
        ]
        return json.dumps(produtos)

    products: list[Product] = []
    url = f"{get_settings().shopify.base_url}/products.json"
    params: dict = {
        "status": "active",
        "limit": 250,
        "fields": "id,title,product_type,vendor,status,variants,created_at,updated_at",
    }

    with httpx.Client(timeout=30.0) as client:
        while True:
            response = client.get(url, params=params, headers=_headers())
            response.raise_for_status()
            batch = ProductsResponse.model_validate(response.json())
            products.extend(batch.products)

            link_header = response.headers.get("Link", "")
            next_url = _parse_next_link(link_header)
            if not next_url:
                break
            url = next_url
            params = {}

    return json.dumps([p.model_dump(mode="json") for p in products])

"""
Testes da Shopify tool com mock HTTP via pytest-httpx.
Não fazem chamadas reais à API.
"""

import json
import re
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import SAMPLE_ORDERS, SAMPLE_PRODUCTS

TEST_BASE_URL = "https://test-store.myshopify.com/admin/api/2024-01"
PAGE2_URL = "https://test-store.myshopify.com/next?page_info=abc"

ORDERS_URL_PATTERN = re.compile(rf"{re.escape(TEST_BASE_URL)}/orders\.json.*")
PRODUCTS_URL_PATTERN = re.compile(rf"{re.escape(TEST_BASE_URL)}/products\.json.*")


@pytest.fixture(autouse=True)
def mock_shopify_settings():
    """Injeta configurações Shopify fake em todos os testes deste módulo."""
    mock_s = MagicMock()
    mock_s.shopify.access_token = "shpat_test_token"
    mock_s.shopify.base_url = TEST_BASE_URL
    mock_s.shopify_demo_mode = False  # garante que os testes testam o caminho HTTP real

    with patch("sales_agent.tools.shopify_tool.get_settings", return_value=mock_s):
        yield


class TestFetchOrders:
    def test_returns_orders_json(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url=ORDERS_URL_PATTERN,
            json={"orders": SAMPLE_ORDERS},
            headers={"Link": ""},
        )

        from sales_agent.tools.shopify_tool import fetch_orders
        result = fetch_orders.run(start_date="2025-04-01", end_date="2025-04-30", status="paid")

        orders = json.loads(result)
        assert len(orders) == 2
        assert orders[0]["order_number"] == 1001

    def test_handles_pagination(self, httpx_mock) -> None:
        page1 = [SAMPLE_ORDERS[0]]
        page2 = [SAMPLE_ORDERS[1]]

        httpx_mock.add_response(
            url=ORDERS_URL_PATTERN,
            json={"orders": page1},
            headers={"Link": f'<{PAGE2_URL}>; rel="next"'},
        )
        httpx_mock.add_response(
            url=PAGE2_URL,
            json={"orders": page2},
            headers={"Link": ""},
        )

        from sales_agent.tools.shopify_tool import fetch_orders
        result = fetch_orders.run(start_date="2025-04-01", end_date="2025-04-30")

        orders = json.loads(result)
        assert len(orders) == 2

    def test_invalid_dates_use_defaults(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url=ORDERS_URL_PATTERN,
            json={"orders": []},
            headers={"Link": ""},
        )

        from sales_agent.tools.shopify_tool import fetch_orders
        result = fetch_orders.run(start_date="data-invalida", end_date="outra-invalida")

        assert result == "[]"


class TestFetchProducts:
    def test_returns_products_json(self, httpx_mock) -> None:
        httpx_mock.add_response(
            url=PRODUCTS_URL_PATTERN,
            json={"products": SAMPLE_PRODUCTS},
            headers={"Link": ""},
        )

        from sales_agent.tools.shopify_tool import fetch_products
        result = fetch_products.run()

        products = json.loads(result)
        assert len(products) == 1
        assert products[0]["title"] == "Camiseta Premium"

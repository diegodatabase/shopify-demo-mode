"""Fixtures compartilhadas entre todos os testes."""

import json
from decimal import Decimal

import pytest


SAMPLE_ORDERS = [
    {
        "id": 1001,
        "order_number": 1001,
        "created_at": "2025-04-10T14:30:00-03:00",
        "currency": "BRL",
        "total_price": "299.90",
        "subtotal_price": "299.90",
        "financial_status": "paid",
        "fulfillment_status": "fulfilled",
        "shipping_address": {
            "city": "São Paulo",
            "province": "São Paulo",
            "province_code": "SP",
            "country": "Brazil",
            "country_code": "BR",
        },
        "line_items": [
            {
                "id": 2001,
                "product_id": 3001,
                "variant_id": 4001,
                "title": "Camiseta Premium",
                "quantity": 2,
                "price": "99.95",
                "sku": "CAM-001",
                "product_type": "Vestuário",
                "vendor": "Marca A",
            },
            {
                "id": 2002,
                "product_id": 3002,
                "variant_id": 4002,
                "title": "Tênis Running",
                "quantity": 1,
                "price": "100.00",
                "sku": "TEN-001",
                "product_type": "Calçados",
                "vendor": "Marca B",
            },
        ],
    },
    {
        "id": 1002,
        "order_number": 1002,
        "created_at": "2025-04-11T10:00:00-03:00",
        "currency": "BRL",
        "total_price": "199.90",
        "subtotal_price": "199.90",
        "financial_status": "paid",
        "fulfillment_status": None,
        "shipping_address": {
            "city": "Rio de Janeiro",
            "province": "Rio de Janeiro",
            "province_code": "RJ",
            "country": "Brazil",
            "country_code": "BR",
        },
        "line_items": [
            {
                "id": 2003,
                "product_id": 3001,
                "variant_id": 4003,
                "title": "Camiseta Premium",
                "quantity": 1,
                "price": "99.95",
                "sku": "CAM-002",
                "product_type": "Vestuário",
                "vendor": "Marca A",
            },
            {
                "id": 2004,
                "product_id": 3003,
                "variant_id": 4004,
                "title": "Boné Strapback",
                "quantity": 1,
                "price": "99.95",
                "sku": "BON-001",
                "product_type": "Acessórios",
                "vendor": "Marca A",
            },
        ],
    },
]

SAMPLE_PRODUCTS = [
    {
        "id": 3001,
        "title": "Camiseta Premium",
        "product_type": "Vestuário",
        "vendor": "Marca A",
        "status": "active",
        "created_at": "2024-01-01T00:00:00-03:00",
        "updated_at": "2025-01-01T00:00:00-03:00",
        "variants": [
            {"id": 4001, "title": "P", "price": "99.95", "sku": "CAM-001", "inventory_quantity": 50},
            {"id": 4003, "title": "M", "price": "99.95", "sku": "CAM-002", "inventory_quantity": 30},
        ],
    },
]


@pytest.fixture
def sample_orders_json() -> str:
    return json.dumps({"orders": SAMPLE_ORDERS})


@pytest.fixture
def sample_orders_list_json() -> str:
    return json.dumps(SAMPLE_ORDERS)

"""
Gerador de dados de vendas fictícios para modo demo.

Simula uma loja brasileira de moda/esportes com pedidos dos últimos 6 meses.
Seed fixo garante dados reproduzíveis entre execuções.
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

SEED = 42

PRODUTOS = [
    {"title": "Camiseta Básica Algodão",     "product_type": "Vestuário",   "vendor": "UrbanWear",   "price": 89.90},
    {"title": "Camiseta Premium Dry-Fit",    "product_type": "Vestuário",   "vendor": "UrbanWear",   "price": 129.90},
    {"title": "Calça Jeans Slim",            "product_type": "Vestuário",   "vendor": "DenimBR",     "price": 249.90},
    {"title": "Calça Moletom Jogger",        "product_type": "Vestuário",   "vendor": "UrbanWear",   "price": 179.90},
    {"title": "Shorts Academia",             "product_type": "Vestuário",   "vendor": "SportMax",    "price": 99.90},
    {"title": "Tênis Running Pro",           "product_type": "Calçados",    "vendor": "SportMax",    "price": 399.90},
    {"title": "Tênis Casual Lifestyle",      "product_type": "Calçados",    "vendor": "UrbanStep",   "price": 299.90},
    {"title": "Chinelo Slide Premium",       "product_type": "Calçados",    "vendor": "UrbanStep",   "price": 89.90},
    {"title": "Boné Strapback",              "product_type": "Acessórios",  "vendor": "UrbanWear",   "price": 79.90},
    {"title": "Mochila Impermeável 25L",     "product_type": "Acessórios",  "vendor": "TrailGear",   "price": 219.90},
    {"title": "Meias Kit 3 Pares",           "product_type": "Acessórios",  "vendor": "ComfortSock", "price": 49.90},
    {"title": "Fone Bluetooth Sport",        "product_type": "Eletrônicos", "vendor": "TechAudio",   "price": 349.90},
    {"title": "Smartwatch Fitness",          "product_type": "Eletrônicos", "vendor": "TechAudio",   "price": 599.90},
    {"title": "Garrafa Térmica 1L",          "product_type": "Acessórios",  "vendor": "TrailGear",   "price": 129.90},
    {"title": "Bermuda Tactel",              "product_type": "Vestuário",   "vendor": "SportMax",    "price": 119.90},
]

# Distribuição geográfica realista do e-commerce brasileiro
ESTADOS = [
    ("SP", "São Paulo",         0.32),
    ("RJ", "Rio de Janeiro",    0.15),
    ("MG", "Belo Horizonte",    0.12),
    ("RS", "Porto Alegre",      0.08),
    ("PR", "Curitiba",          0.07),
    ("SC", "Florianópolis",     0.06),
    ("BA", "Salvador",          0.05),
    ("GO", "Goiânia",           0.04),
    ("PE", "Recife",            0.04),
    ("CE", "Fortaleza",         0.04),
    ("AM", "Manaus",            0.02),
    ("PA", "Belém",             0.01),
]

STATUS = ["paid"] * 85 + ["refunded"] * 8 + ["pending"] * 7  # 85% paid


def _weighted_choice(options_with_weights: list[tuple]) -> tuple:
    items = [o[:-1] for o in options_with_weights]
    weights = [o[-1] for o in options_with_weights]
    return random.choices(items, weights=weights, k=1)[0]


def gerar_pedidos(
    start_date: datetime,
    end_date: datetime,
    n_pedidos: int = 150,
) -> list[dict]:
    """
    Gera lista de pedidos fictícios no formato da Shopify API.

    Args:
        start_date: Data inicial do período.
        end_date: Data final do período.
        n_pedidos: Número de pedidos a gerar.
    """
    rng = random.Random(SEED)
    periodo_segundos = int((end_date - start_date).total_seconds())
    pedidos = []

    for i in range(n_pedidos):
        # Data aleatória no período com viés para fins de semana
        delta = rng.randint(0, periodo_segundos)
        created_at = start_date + timedelta(seconds=delta)

        estado_info = _weighted_choice(ESTADOS)
        province_code, city = estado_info[0], estado_info[1]

        # 1 a 3 itens por pedido
        n_itens = rng.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        produtos_escolhidos = rng.sample(PRODUTOS, k=min(n_itens, len(PRODUTOS)))

        line_items = []
        subtotal = Decimal("0")
        for j, prod in enumerate(produtos_escolhidos):
            qty = rng.choices([1, 2], weights=[0.85, 0.15])[0]
            preco = Decimal(str(prod["price"]))
            subtotal += preco * qty
            line_items.append({
                "id": (i + 1) * 100 + j,
                "product_id": PRODUTOS.index(prod) + 1000,
                "variant_id": (PRODUTOS.index(prod) + 1000) * 10,
                "title": prod["title"],
                "quantity": qty,
                "price": str(preco),
                "sku": f"SKU-{PRODUTOS.index(prod)+1:03d}-{j}",
                "product_type": prod["product_type"],
                "vendor": prod["vendor"],
            })

        status = rng.choice(STATUS)
        pedidos.append({
            "id": 10000 + i,
            "order_number": 1000 + i,
            "created_at": created_at.isoformat(),
            "currency": "BRL",
            "total_price": str(subtotal),
            "subtotal_price": str(subtotal),
            "financial_status": status,
            "fulfillment_status": "fulfilled" if status == "paid" else None,
            "shipping_address": {
                "city": city,
                "province": province_code,
                "province_code": province_code,
                "country": "Brazil",
                "country_code": "BR",
            },
            "line_items": line_items,
        })

    # Ordenar por data
    pedidos.sort(key=lambda p: p["created_at"])
    return pedidos

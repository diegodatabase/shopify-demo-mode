"""
Tools de análise de dados de vendas.

Recebem JSON de pedidos (saída do fetch_orders), processam com pandas
e retornam tabelas markdown prontas para o agente interpretar.
"""

import json
from decimal import Decimal

import pandas as pd
from crewai.tools import tool


def _orders_to_dataframe(orders_json: str) -> pd.DataFrame:
    """Transforma o JSON de pedidos em um DataFrame com uma linha por line_item."""
    orders = json.loads(orders_json)
    rows = []

    for order in orders:
        shipping = order.get("shipping_address") or {}
        state = shipping.get("province_code") or "N/A"
        city = shipping.get("city") or "N/A"

        for item in order.get("line_items", []):
            rows.append({
                "order_id": order["id"],
                "order_number": order["order_number"],
                "created_at": order["created_at"],
                "financial_status": order["financial_status"],
                "product_title": item["title"],
                "product_type": item.get("product_type") or "Sem categoria",
                "vendor": item.get("vendor") or "N/A",
                "quantity": int(item["quantity"]),
                "unit_price": float(item["price"]),
                "revenue": float(item["price"]) * int(item["quantity"]),
                "state": state,
                "city": city,
                "currency": order["currency"],
            })

    return pd.DataFrame(rows)


def _to_markdown_table(df: pd.DataFrame) -> str:
    """Converte DataFrame para tabela markdown."""
    if df.empty:
        return "Nenhum dado encontrado."
    return df.to_markdown(index=False, floatfmt=".2f")


@tool("group_by_product")
def group_by_product(orders_json: str, top_n: int = 10) -> str:
    """
    Agrupa pedidos por produto e retorna ranking de receita.

    Args:
        orders_json: JSON serializado com lista de pedidos (saída do fetch_orders).
        top_n: Quantos produtos retornar no ranking. Padrão: 10.

    Returns:
        Tabela markdown com produto, unidades vendidas e receita total.
    """
    df = _orders_to_dataframe(orders_json)
    if df.empty:
        return "Nenhum pedido encontrado para análise."

    grouped = (
        df.groupby(["product_title", "product_type", "vendor"])
        .agg(
            unidades_vendidas=("quantity", "sum"),
            receita_total=("revenue", "sum"),
            num_pedidos=("order_id", "nunique"),
        )
        .reset_index()
        .sort_values("receita_total", ascending=False)
        .head(int(top_n))
    )

    grouped["receita_total"] = grouped["receita_total"].map("R$ {:,.2f}".format)
    grouped.columns = ["Produto", "Categoria", "Fornecedor", "Unidades", "Receita Total", "Nº Pedidos"]

    return f"### Top {top_n} Produtos por Receita\n\n{_to_markdown_table(grouped)}"


@tool("group_by_region")
def group_by_region(orders_json: str) -> str:
    """
    Agrupa pedidos por estado (UF) e retorna distribuição geográfica de vendas.

    Args:
        orders_json: JSON serializado com lista de pedidos (saída do fetch_orders).

    Returns:
        Tabela markdown com estado, número de pedidos e receita total.
    """
    df = _orders_to_dataframe(orders_json)
    if df.empty:
        return "Nenhum pedido encontrado para análise."

    # Receita a nível de pedido (não duplicar por line_item)
    orders_df = (
        df.groupby(["order_id", "state", "city"])
        .agg(order_total=("revenue", "sum"))
        .reset_index()
    )

    by_state = (
        orders_df.groupby("state")
        .agg(
            num_pedidos=("order_id", "count"),
            receita_total=("order_total", "sum"),
        )
        .reset_index()
        .sort_values("receita_total", ascending=False)
    )

    by_state["receita_total"] = by_state["receita_total"].map("R$ {:,.2f}".format)
    by_state["participacao_pct"] = (
        orders_df.groupby("state")["order_total"].sum()
        / orders_df["order_total"].sum()
        * 100
    ).reindex(by_state["state"]).values
    by_state["participacao_pct"] = by_state["participacao_pct"].map("{:.1f}%".format)

    by_state.columns = ["Estado (UF)", "Nº Pedidos", "Receita Total", "% do Total"]

    return f"### Distribuição de Vendas por Estado\n\n{_to_markdown_table(by_state)}"


@tool("group_by_category")
def group_by_category(orders_json: str) -> str:
    """
    Agrupa pedidos por categoria de produto.

    Args:
        orders_json: JSON serializado com lista de pedidos (saída do fetch_orders).

    Returns:
        Tabela markdown com categoria, unidades vendidas e receita total.
    """
    df = _orders_to_dataframe(orders_json)
    if df.empty:
        return "Nenhum pedido encontrado para análise."

    grouped = (
        df.groupby("product_type")
        .agg(
            unidades=("quantity", "sum"),
            receita_total=("revenue", "sum"),
            num_produtos=("product_title", "nunique"),
        )
        .reset_index()
        .sort_values("receita_total", ascending=False)
    )

    grouped["receita_total"] = grouped["receita_total"].map("R$ {:,.2f}".format)
    grouped.columns = ["Categoria", "Unidades", "Receita Total", "Produtos Únicos"]

    return f"### Vendas por Categoria\n\n{_to_markdown_table(grouped)}"

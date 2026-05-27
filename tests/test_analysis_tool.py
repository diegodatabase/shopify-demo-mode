"""
Testes das analysis tools com DataFrames fixos.
Não requerem API real nem LLM.
"""

import json

import pytest

from sales_agent.tools.analysis_tool import group_by_category, group_by_product, group_by_region


class TestGroupByProduct:
    def test_returns_markdown_table(self, sample_orders_list_json: str) -> None:
        result = group_by_product.run(orders_json=sample_orders_list_json, top_n=10)
        assert "### Top" in result
        assert "Produto" in result
        assert "Receita Total" in result

    def test_camiseta_is_top_product(self, sample_orders_list_json: str) -> None:
        result = group_by_product.run(orders_json=sample_orders_list_json, top_n=10)
        assert "Camiseta Premium" in result

    def test_top_n_limits_results(self, sample_orders_list_json: str) -> None:
        result = group_by_product.run(orders_json=sample_orders_list_json, top_n=1)
        assert "Top 1" in result

    def test_empty_orders(self) -> None:
        result = group_by_product.run(orders_json=json.dumps([]), top_n=10)
        assert "Nenhum pedido" in result


class TestGroupByRegion:
    def test_returns_state_breakdown(self, sample_orders_list_json: str) -> None:
        result = group_by_region.run(orders_json=sample_orders_list_json)
        assert "SP" in result
        assert "RJ" in result

    def test_has_percentage_column(self, sample_orders_list_json: str) -> None:
        result = group_by_region.run(orders_json=sample_orders_list_json)
        assert "%" in result

    def test_empty_orders(self) -> None:
        result = group_by_region.run(orders_json=json.dumps([]))
        assert "Nenhum pedido" in result


class TestGroupByCategory:
    def test_groups_by_product_type(self, sample_orders_list_json: str) -> None:
        result = group_by_category.run(orders_json=sample_orders_list_json)
        assert "Vestuário" in result
        assert "Calçados" in result
        assert "Acessórios" in result

    def test_vestuario_has_highest_revenue(self, sample_orders_list_json: str) -> None:
        result = group_by_category.run(orders_json=sample_orders_list_json)
        lines = result.split("\n")
        data_lines = [l for l in lines if "Vestuário" in l or "Calçados" in l or "Acessórios" in l]
        assert data_lines[0].startswith("| Vestuário")

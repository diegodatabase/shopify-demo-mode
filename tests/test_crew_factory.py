"""
Testes da CrewFactory — verifica estrutura dos Crews sem executar o LLM.
"""

from unittest.mock import MagicMock

import pytest

from sales_agent.factory.agent_factory import AgentFactory, AgentRole
from sales_agent.factory.crew_factory import CrewFactory


@pytest.fixture
def mock_settings():
    s = MagicMock()
    s.llm.model = "gpt-4o-mini"
    s.llm.api_key = "sk-test"
    s.agent.verbose = False
    return s


@pytest.fixture
def crew_factory(mock_settings):
    factory = AgentFactory(mock_settings)
    return CrewFactory(factory)


class TestAnalysisCrew:
    def test_has_two_agents(self, crew_factory: CrewFactory) -> None:
        crew = crew_factory.build_analysis_crew(
            query="Quais produtos mais venderam?",
            date_range=("2025-04-01", "2025-04-30"),
        )
        assert len(crew.agents) == 2

    def test_has_two_tasks(self, crew_factory: CrewFactory) -> None:
        crew = crew_factory.build_analysis_crew(
            query="Top produtos por região",
            date_range=("2025-04-01", "2025-04-30"),
        )
        assert len(crew.tasks) == 2

    def test_query_in_analysis_task(self, crew_factory: CrewFactory) -> None:
        query = "Quais estados têm mais vendas?"
        crew = crew_factory.build_analysis_crew(
            query=query,
            date_range=("2025-04-01", "2025-04-30"),
        )
        assert query in crew.tasks[1].description


class TestReportCrew:
    def test_has_three_agents(self, crew_factory: CrewFactory) -> None:
        crew = crew_factory.build_report_crew(month="2025-04")
        assert len(crew.agents) == 3

    def test_has_three_tasks(self, crew_factory: CrewFactory) -> None:
        crew = crew_factory.build_report_crew(month="2025-04")
        assert len(crew.tasks) == 3

    def test_correct_date_range_for_april(self, crew_factory: CrewFactory) -> None:
        crew = crew_factory.build_report_crew(month="2025-04")
        fetch_task_desc = crew.tasks[0].description
        assert "2025-04-01" in fetch_task_desc
        assert "2025-04-30" in fetch_task_desc

    def test_correct_date_range_for_february_leap_year(self, crew_factory: CrewFactory) -> None:
        crew = crew_factory.build_report_crew(month="2024-02")
        fetch_task_desc = crew.tasks[0].description
        assert "2024-02-29" in fetch_task_desc

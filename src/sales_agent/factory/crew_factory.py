"""
CrewFactory: monta o Crew correto para cada tipo de query.

Separa dois fluxos:
- analysis_crew: DataFetcher → Analyst (resposta direta ao usuário)
- report_crew:   DataFetcher → Analyst → Reporter (salva arquivo .md)
"""

from crewai import Crew, Process, Task

from sales_agent.factory.agent_factory import AgentFactory, AgentRole


class CrewFactory:
    def __init__(self, agent_factory: AgentFactory) -> None:
        self._factory = agent_factory

    def build_analysis_crew(self, query: str, date_range: tuple[str, str]) -> Crew:
        """
        Crew para perguntas interativas.
        Retorna análise em texto sem salvar relatório.

        Args:
            query: Pergunta do usuário em linguagem natural.
            date_range: Tupla (start_date, end_date) no formato YYYY-MM-DD.
        """
        start_date, end_date = date_range
        fetcher = self._factory.create(AgentRole.DATA_FETCHER)
        analyst = self._factory.create(AgentRole.ANALYST)

        fetch_task = Task(
            description=(
                f"Busque todos os pedidos com status 'paid' entre {start_date} e {end_date} "
                "usando fetch_orders. Em seguida, salve os pedidos no banco de dados usando "
                "save_orders_to_db. Retorne o JSON completo dos pedidos."
            ),
            expected_output="JSON serializado com lista de pedidos da Shopify.",
            agent=fetcher,
        )

        analysis_task = Task(
            description=(
                f"Com os pedidos fornecidos, responda a seguinte pergunta:\n\n"
                f"'{query}'\n\n"
                "Use as tools disponíveis para agrupar os dados adequadamente. "
                "Apresente tabelas e insights objetivos."
            ),
            expected_output=(
                "Análise completa em markdown com tabelas e insights principais. "
                "Responda diretamente à pergunta do usuário."
            ),
            agent=analyst,
            context=[fetch_task],
        )

        return Crew(
            agents=[fetcher, analyst],
            tasks=[fetch_task, analysis_task],
            process=Process.sequential,
            verbose=True,
        )

    def build_report_crew(self, month: str) -> Crew:
        """
        Crew para geração de relatório mensal completo.
        Salva arquivo .md em reports/.

        Args:
            month: Mês no formato YYYY-MM.
        """
        import calendar
        from datetime import date

        year, mon = int(month[:4]), int(month[5:7])
        last_day = calendar.monthrange(year, mon)[1]
        start_date = f"{month}-01"
        end_date = f"{month}-{last_day:02d}"
        filename = f"relatorio_{month.replace('-', '_')}"

        fetcher = self._factory.create(AgentRole.DATA_FETCHER)
        analyst = self._factory.create(AgentRole.ANALYST)
        reporter = self._factory.create(AgentRole.REPORTER)

        fetch_task = Task(
            description=(
                f"Busque todos os pedidos com status 'paid' entre {start_date} e {end_date} "
                "usando fetch_orders. Em seguida, salve os pedidos no banco de dados usando "
                "save_orders_to_db. Retorne o JSON completo dos pedidos."
            ),
            expected_output="JSON serializado com lista de pedidos.",
            agent=fetcher,
        )

        analysis_task = Task(
            description=(
                f"Analise os pedidos do mês {month}. "
                "Gere: (1) top 10 produtos por receita, "
                "(2) distribuição por estado, "
                "(3) vendas por categoria. "
                "Inclua totais gerais (receita total, número de pedidos, ticket médio)."
            ),
            expected_output=(
                "Análise completa em markdown com seções separadas para "
                "produtos, regiões, categorias e resumo geral."
            ),
            agent=analyst,
            context=[fetch_task],
        )

        report_task = Task(
            description=(
                f"Formate as análises em um relatório executivo para o mês {month}. "
                "Inclua: sumário executivo (3-5 bullets), seções de análise, "
                "e recomendações práticas. "
                f"Salve o relatório com o nome '{filename}'."
            ),
            expected_output=f"Caminho do arquivo salvo em reports/{filename}.md",
            agent=reporter,
            context=[analysis_task],
        )

        return Crew(
            agents=[fetcher, analyst, reporter],
            tasks=[fetch_task, analysis_task, report_task],
            process=Process.sequential,
            verbose=True,
        )

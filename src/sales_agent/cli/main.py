"""
CLI do Sales Agent — dois modos de operação:

  sales-agent ask "Quais produtos mais venderam no RJ?"
  sales-agent report --month 2025-04
"""

from datetime import date, timedelta

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner

from sales_agent.config.settings import get_settings
from sales_agent.factory.agent_factory import AgentFactory
from sales_agent.factory.crew_factory import CrewFactory

app = typer.Typer(
    name="sales-agent",
    help="Agente de análise de vendas Shopify powered by CrewAI + Claude.",
    add_completion=False,
)
console = Console()


def _build_crew_factory() -> CrewFactory:
    agent_factory = AgentFactory(get_settings())
    return CrewFactory(agent_factory)


def _default_date_range() -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=30)
    return str(start), str(end)


@app.command()
def ask(
    query: str = typer.Argument(..., help="Pergunta em linguagem natural sobre suas vendas."),
    start_date: str = typer.Option("", "--start", "-s", help="Data inicial YYYY-MM-DD."),
    end_date: str = typer.Option("", "--end", "-e", help="Data final YYYY-MM-DD."),
) -> None:
    """Faça uma pergunta sobre suas vendas e receba análise interativa."""
    if not start_date or not end_date:
        start_date, end_date = _default_date_range()
        console.print(
            f"[dim]Usando período padrão: {start_date} → {end_date}[/dim]"
        )

    console.print(
        Panel.fit(
            f"[bold cyan]Pergunta:[/bold cyan] {query}\n"
            f"[dim]Período: {start_date} → {end_date}[/dim]",
            title="Sales Agent",
        )
    )

    crew_factory = _build_crew_factory()
    crew = crew_factory.build_analysis_crew(query, (start_date, end_date))

    with console.status("[bold green]Analisando vendas...[/bold green]", spinner="dots"):
        result = crew.kickoff()

    console.print("\n")
    console.print(Markdown(str(result)))


@app.command()
def report(
    month: str = typer.Option(
        ...,
        "--month",
        "-m",
        help="Mês do relatório no formato YYYY-MM.",
        prompt="Mês do relatório (YYYY-MM)",
    ),
) -> None:
    """Gera relatório mensal completo e salva em reports/."""
    # Valida formato
    try:
        date.fromisoformat(f"{month}-01")
    except ValueError:
        console.print(f"[red]Formato inválido:[/red] use YYYY-MM (ex: 2025-04)")
        raise typer.Exit(code=1)

    console.print(
        Panel.fit(
            f"[bold cyan]Gerando relatório de[/bold cyan] {month}",
            title="Sales Agent — Relatório",
        )
    )

    crew_factory = _build_crew_factory()
    crew = crew_factory.build_report_crew(month)

    with console.status("[bold green]Gerando relatório...[/bold green]", spinner="dots"):
        result = crew.kickoff()

    console.print(f"\n[bold green]Relatório salvo em:[/bold green] {result}")


@app.command()
def interactive() -> None:
    """Modo interativo: loop de perguntas até digitar 'sair'."""
    start_date, end_date = _default_date_range()
    crew_factory = _build_crew_factory()

    console.print(
        Panel(
            "[bold]Sales Agent — Modo Interativo[/bold]\n"
            f"[dim]Período: {start_date} → {end_date}[/dim]\n"
            "[dim]Digite 'sair' para encerrar.[/dim]",
            title="Sales Agent",
        )
    )

    while True:
        query = Prompt.ask("\n[bold cyan]Pergunta[/bold cyan]")
        if query.lower() in ("sair", "exit", "quit"):
            console.print("[dim]Encerrando...[/dim]")
            break

        crew = crew_factory.build_analysis_crew(query, (start_date, end_date))

        with console.status("[bold green]Analisando...[/bold green]", spinner="dots"):
            result = crew.kickoff()

        console.print("\n")
        console.print(Markdown(str(result)))


if __name__ == "__main__":
    app()

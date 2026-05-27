import re
from datetime import datetime
from pathlib import Path

from crewai.tools import tool

REPORTS_DIR = Path(__file__).parents[4] / "reports"


@tool("save_report")
def save_report(content: str, filename: str = "") -> str:
    """
    Salva o conteúdo do relatório como arquivo markdown em reports/.

    Args:
        content: Conteúdo markdown do relatório.
        filename: Nome do arquivo (sem extensão). Se omitido, usa timestamp.

    Returns:
        Caminho absoluto do arquivo salvo.
    """
    REPORTS_DIR.mkdir(exist_ok=True)

    if not filename:
        filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Sanitiza o nome do arquivo
    safe_name = re.sub(r"[^\w\-]", "_", filename)
    path = REPORTS_DIR / f"{safe_name}.md"
    path.write_text(content, encoding="utf-8")

    return str(path.resolve())

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Instalar dependências
uv sync

# Subir o PostgreSQL local
docker compose up -d

# Aplicar migrations do banco
uv run alembic upgrade head

# Gerar nova migration após alterar ORM models
uv run alembic revision --autogenerate -m "descricao"

# Rodar o agente (modo pergunta direta)
uv run sales-agent ask "Quais produtos mais venderam no mês passado?"

# Com período específico
uv run sales-agent ask "Top regiões por receita" --start 2025-04-01 --end 2025-04-30

# Modo interativo (loop de perguntas)
uv run sales-agent interactive

# Gerar relatório mensal (salva em reports/)
uv run sales-agent report --month 2025-04

# Rodar todos os testes
uv run pytest

# Rodar um teste específico
uv run pytest tests/test_analysis_tool.py::TestGroupByProduct::test_camiseta_is_top_product -v
```

## Setup

1. Copie `.env.example` para `.env` e preencha:
   - `SHOPIFY_SHOP_DOMAIN` — ex: `minha-loja.myshopify.com`
   - `SHOPIFY_ACCESS_TOKEN` — token do Private App (Admin → Apps → Develop apps)
   - `OPENAI_API_KEY` — chave da API OpenAI
   - `DATABASE_URL` — padrão já apontado para o Docker local

2. `docker compose up -d` — sobe o PostgreSQL
3. `uv run alembic upgrade head` — cria as tabelas

## Architecture

Sistema multi-agente com CrewAI e 3 agentes em pipeline sequencial:

```
fetch_orders ──→ save_orders_to_db   →   group_by_*   →   save_report
(ShopifyTool)      (DBTool)            (AnalysisTool)    (ReportTool)
      │               │                      │                │
      └───────────────┘                      │                │
         DataFetcherAgent           SalesAnalystAgent   ReportWriterAgent
                └──────────────────────────┴──────────────────┘
                                       Crew
                                        │
                                  CrewFactory
                            (build_analysis_crew /
                             build_report_crew)
```

**Regra de ouro**: tools são funções determinísticas (`@tool`); agentes decidem quando e como chamá-las. Nunca coloque lógica de negócio dentro de um agente.

### Diretórios

| Caminho | Responsabilidade |
|---|---|
| `src/sales_agent/tools/` | Funções `@tool` — únicas que tocam API, banco ou disco |
| `src/sales_agent/agents/` | Definição de `role/goal/backstory/tools` — sem instanciação |
| `src/sales_agent/factory/` | `AgentFactory` (instancia agentes) + `CrewFactory` (monta crews) |
| `src/sales_agent/models/` | Pydantic models para boundary da Shopify API |
| `src/sales_agent/db/` | ORM models, session factory, OrderRepository |
| `src/sales_agent/config/` | `settings.py` — pydantic-settings lendo de `.env` |
| `src/sales_agent/cli/` | CLI typer com comandos `ask`, `report`, `interactive` |
| `alembic/` | Migrations do banco — nunca editar `versions/` manualmente |
| `reports/` | Relatórios markdown gerados pelo agente |

### Fluxo de dados

1. `fetch_orders()` → Shopify REST API → Pydantic `Order` → JSON
2. `save_orders_to_db()` → `OrderRepository.upsert_orders()` → PostgreSQL (upsert por ID)
3. `group_by_*()` → JSON de orders → pandas groupby → markdown table
4. `load_orders_from_db()` → PostgreSQL → JSON (mesmo formato do fetch_orders)
5. `save_report()` → markdown → `reports/*.md`

### Banco de dados

- ORM: SQLAlchemy 2 com `mapped_column` e type hints modernos
- Migrations: Alembic autogenerate a partir do `Base.metadata` em `db/models.py`
- Acesso: sempre via `get_session()` context manager (garante commit/rollback)
- Repositório: `OrderRepository` isola as queries — tools nunca tocam ORM diretamente
- Tabelas: `orders` (dados do pedido + endereço desnormalizado) + `line_items` (FK para orders)

### Factory Pattern

- `AgentFactory.create(AgentRole)` → instancia Agent com model string (LiteLLM) + tools injetados
- `CrewFactory.build_analysis_crew()` → 2 agentes, sem salvar arquivo (resposta direta)
- `CrewFactory.build_report_crew()` → 3 agentes, inclui ReportWriter que salva `.md`

### Paginação Shopify

A Shopify usa cursor-based pagination (header `Link`). `_fetch_all_orders()` em `shopify_tool.py` itera até não haver `rel="next"`. Passe `params=None` (não `params={}`) ao seguir cursor URLs — httpx sobrescreve a query string se receber um dict vazio.

## Testing

- Testes de tools: DataFrames/JSON fixos, sem API real (`tests/conftest.py` contém fixtures)
- Testes de HTTP: mock via `pytest-httpx` com `url=re.compile(...)` (não `url__regex`)
- Testes de factory: sem mock de LLM — `AgentFactory` usa string de modelo que o CrewAI aceita
- Testes de banco: não implementados ainda — usar banco de teste separado com `pytest-postgresql`

"""
AgentFactory: ponto único de instanciação de agentes CrewAI.

Injeta LLM, tools e configurações sem que os agentes precisem
conhecer a origem dessas dependências.
"""

from enum import Enum

import os

from crewai import Agent

from sales_agent.agents import analyst, data_fetcher, reporter
from sales_agent.config.settings import Settings


class AgentRole(str, Enum):
    DATA_FETCHER = "data_fetcher"
    ANALYST = "analyst"
    REPORTER = "reporter"


class AgentFactory:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        # CrewAI aceita string de modelo via LiteLLM; a API key é lida do env.
        # Para OpenAI: modelo sem prefix (ex: "gpt-4o-mini").
        # Para Anthropic: prefix "anthropic/" (ex: "anthropic/claude-sonnet-4-6").
        self._model = settings.llm.model
        os.environ.setdefault("OPENAI_API_KEY", settings.llm.api_key or "")

    def create(self, role: AgentRole) -> Agent:
        verbose = self._settings.agent.verbose
        base_kwargs = {"llm": self._model, "verbose": verbose, "memory": False}

        match role:
            case AgentRole.DATA_FETCHER:
                return Agent(
                    role=data_fetcher.ROLE,
                    goal=data_fetcher.GOAL,
                    backstory=data_fetcher.BACKSTORY,
                    tools=data_fetcher.TOOLS,
                    max_iter=5,
                    **base_kwargs,
                )
            case AgentRole.ANALYST:
                return Agent(
                    role=analyst.ROLE,
                    goal=analyst.GOAL,
                    backstory=analyst.BACKSTORY,
                    tools=analyst.TOOLS,
                    max_iter=8,
                    **base_kwargs,
                )
            case AgentRole.REPORTER:
                return Agent(
                    role=reporter.ROLE,
                    goal=reporter.GOAL,
                    backstory=reporter.BACKSTORY,
                    tools=reporter.TOOLS,
                    max_iter=3,
                    **base_kwargs,
                )
            case _:
                raise ValueError(f"Role desconhecido: {role}")

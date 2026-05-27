"""
Configurações da aplicação via pydantic-settings.

ShopifySettings, LLMSettings e AgentSettings são BaseModel comuns — não BaseSettings.
Apenas Settings lê as env vars. Os sub-objetos são expostos via @property,
evitando que a definição da classe avalie credenciais na importação do módulo.
"""

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ShopifySettings(BaseModel):
    shop_domain: str
    access_token: str
    api_version: str = "2024-01"

    @property
    def base_url(self) -> str:
        return f"https://{self.shop_domain}/admin/api/{self.api_version}"


class LLMSettings(BaseModel):
    model: str
    temperature: float
    api_key: str


class AgentSettings(BaseModel):
    verbose: bool


class Settings(BaseSettings):
    # Shopify
    shopify_shop_domain: str = ""
    shopify_access_token: str = ""
    shopify_api_version: str = "2024-01"
    shopify_demo_mode: bool = False  # True = usa dados fictícios locais

    # LLM / OpenAI
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1

    # Database
    database_url: str = "postgresql://sales_agent:sales_agent_pass@localhost:5432/sales_agent"

    # Agente
    agent_verbose: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def shopify(self) -> ShopifySettings:
        return ShopifySettings(
            shop_domain=self.shopify_shop_domain,
            access_token=self.shopify_access_token,
            api_version=self.shopify_api_version,
        )

    @property
    def llm(self) -> LLMSettings:
        return LLMSettings(
            model=self.llm_model,
            temperature=self.llm_temperature,
            api_key=self.openai_api_key,
        )

    @property
    def agent(self) -> AgentSettings:
        return AgentSettings(verbose=self.agent_verbose)


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Lazy singleton — não falha na importação quando .env está ausente."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance

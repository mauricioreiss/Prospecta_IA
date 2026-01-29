"""
Prospecta IA - Configuration
Environment-based settings with Pydantic validation
"""
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    app_name: str = "Prospecta IA"
    app_version: str = "2.0.0"
    debug: bool = False

    # Database - Supabase
    supabase_url: str
    supabase_key: str

    # Tables (multi-tenant support)
    table_leads: str = "leads"
    table_intelligence: str = "lead_intelligence"
    table_interactions: str = "interactions"
    table_clientes: str = "clientes_existentes"

    # External APIs (optional for basic operation)
    apify_token: Optional[str] = None
    openai_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    vapi_api_key: Optional[str] = None

    # n8n/Chatwoot (WhatsApp)
    n8n_webhook_url: Optional[str] = None

    # Chatwoot Integration
    chatwoot_url: str = "https://chat.byduo.com.br"
    chatwoot_token: str = "1XMqgiobnqHmjrQBUHXwKYG4"
    chatwoot_account_id: int = 1
    chatwoot_inbox_id: int = 366  # Prospecta-IA-Teste inbox

    # AI Responder
    booking_link: str = "https://calendly.com/oduo"

    # CORS
    allowed_origins: List[str] = ["*"]

    # Default niche
    default_niche: str = "locadora"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


# Convenience export
settings = get_settings()

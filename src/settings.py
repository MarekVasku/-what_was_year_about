"""
Environment settings and configuration management using Pydantic.
Centralizes all environment variables with validation.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Google Sheets Authentication
    google_sheets_credentials: str = ""
    google_application_credentials: str | None = None

    # Groq LLM API
    groq_api_key: str = ""
    model_blurb: str = "llama-3.1-8b-instant"
    model_analysis: str = "openai/gpt-oss-120b"
    model_json: str = "moonshotai/kimi-k2-instruct"
    groq_model: str | None = None  # Legacy fallback

    # SMTP Email (local feedback testing)
    smtp_email: str | None = None
    smtp_password: str | None = None

    # Webhook (Hugging Face feedback)
    webhook_url: str | None = None

    # Cache
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 10

    # Demo/Development
    demo_email_prefix: str | None = None
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore unexpected environment variables

    @property
    def llm_enabled(self) -> bool:
        """Check if LLM features are enabled (requires API key)."""
        return bool(self.groq_api_key)

    @property
    def feedback_enabled(self) -> bool:
        """Check if feedback submission is enabled (requires webhook or SMTP)."""
        return bool(self.webhook_url or (self.smtp_email and self.smtp_password))

    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is configured."""
        return bool(self.smtp_email and self.smtp_password)


# Global settings instance
settings = Settings()

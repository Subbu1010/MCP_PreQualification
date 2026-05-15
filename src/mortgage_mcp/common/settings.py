"""
MCP references: calculate_dti, calculate_ltv, check_borrower_eligibility, recommend_loan_products,
                 search_mortgage_policy, explain_eligibility_decision
Purpose: Central application settings loaded from environment variables (optional API keys, log level).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration shared across MCP tools (no tool-specific paths here)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    google_api_key: str | None = None
    google_embedding_model: str = "text-embedding-004"
    google_genai_use_vertexai: bool = False
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    gemini_model: str = "gemini-2.0-flash-001"
    mcp_log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazy singleton for settings to avoid repeated env parsing."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

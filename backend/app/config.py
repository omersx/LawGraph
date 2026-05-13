"""Legal AI Agent — Configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Google Gemini ──
    google_api_key: str = ""
    gemini_model: str = "gemini-3.0-flash"

    # ── External Reasoning Model (optional) ──
    # Option A: Another Gemini account (different API key + optional custom model)
    reasoning_gemini_api_key: Optional[str] = None
    reasoning_gemini_model: Optional[str] = None   # defaults to gemini_model if not set
    # Option B: OpenAI-compatible endpoint (fine-tuned model, Vertex, etc.)
    reasoning_model_url: Optional[str] = None
    reasoning_model_api_key: Optional[str] = None

    # ── MCP Servers (local stdio) ──
    mcp_govinfo_server_path: str = ""
    mcp_courtlistener_server_path: str = ""
    courtlistener_api_key: str = ""

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

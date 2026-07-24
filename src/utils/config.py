"""Configuracion central del SEO Agent — lee de .env y expone settings tipados."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_env() -> None:
    """Carga .env desde la raiz del proyecto. No falla si no existe."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_env()


@dataclass(frozen=True)
class LLMConfig:
    """Configuracion del LLM orquestador (DeepSeek)."""
    model: str = field(default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"))
    api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    base_url: str = "https://api.deepseek.com"
    temperature: float = 0.3
    max_tokens: int = 4096


@dataclass(frozen=True)
class WigoloConfig:
    """Configuracion del MCP de Wigolo (local-first, sin API key)."""

    command: str = field(default_factory=lambda: os.getenv("WIGOLO_MCP_COMMAND", "npx"))
    args: list[str] = field(
        default_factory=lambda: (os.getenv("WIGOLO_MCP_ARGS") or "-y wigolo").split()
    )


@dataclass(frozen=True)
class OpenSEOConfig:
    """Configuracion del MCP de OpenSEO (self-hosted Docker)."""

    mcp_url: str = field(
        default_factory=lambda: os.getenv("OPENSEO_MCP_URL", "http://localhost:3001/mcp")
    )
    dataforseo_key: str = field(
        default_factory=lambda: os.getenv("DATAFORSEO_API_KEY", "")
    )


@dataclass(frozen=True)
class PageSpeedConfig:
    """Configuracion de Google PageSpeed Insights API."""

    api_key: str = field(
        default_factory=lambda: os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
    )
    base_url: str = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


@dataclass(frozen=True)
class Config:
    """Configuracion completa del SEO Agent."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    wigolo: WigoloConfig = field(default_factory=WigoloConfig)
    openseo: OpenSEOConfig = field(default_factory=OpenSEOConfig)
    pagespeed: PageSpeedConfig = field(default_factory=PageSpeedConfig)
    project_root: Path = PROJECT_ROOT


# Singleton inmutable — importar desde cualquier modulo
config = Config()

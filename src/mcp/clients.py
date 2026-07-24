"""
Clientes MCP para Wigolo y OpenSEO.

Cada cliente es un async context manager que:
  1. Conecta al servidor MCP
  2. Inicializa la sesion
  3. Expone metodos tipados para cada tool
  4. Cierra limpiamente al salir
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

from src.utils.config import config

logger = logging.getLogger(__name__)


# ============================================================
# Wigolo MCP Client (local, stdio)
# ============================================================

@asynccontextmanager
async def wigolo_session() -> AsyncIterator[ClientSession]:
    """Conecta a Wigolo via stdio (proceso local npx -y wigolo)."""
    server_params = StdioServerParameters(
        command=config.wigolo.command,
        args=config.wigolo.args,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("Wigolo MCP conectado")
            yield session


class WigoloClient:
    """Wrapper tipado sobre las tools MCP de Wigolo."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def search(
        self, query: str | list[str], *, max_results: int = 10, **kwargs
    ) -> dict:
        """Busqueda multi-engine con reranking local."""
        params: dict = {"query": query, "max_results": max_results}
        params.update(kwargs)
        result = await self._session.call_tool("search", params)
        return _parse_tool_result(result)

    async def fetch(self, url: str, *, format: str = "markdown", **kwargs) -> dict:
        """Carga una URL con auto-escalado a headless browser."""
        params: dict = {"url": url, "format": format}
        params.update(kwargs)
        result = await self._session.call_tool("fetch", params)
        return _parse_tool_result(result)

    async def crawl(
        self, url: str, *, mode: str = "bfs", max_pages: int = 20, **kwargs
    ) -> dict:
        """Crawl multi-pagina (BFS/DFS/sitemap)."""
        params: dict = {"url": url, "mode": mode, "max_pages": max_pages}
        params.update(kwargs)
        result = await self._session.call_tool("crawl", params)
        return _parse_tool_result(result)

    async def extract(self, url: str, *, schema: str | dict | None = None, **kwargs) -> dict:
        """Extrae datos estructurados de una pagina."""
        params: dict = {"url": url}
        if schema:
            params["schema"] = schema
        params.update(kwargs)
        result = await self._session.call_tool("extract", params)
        return _parse_tool_result(result)

    async def research(self, question: str, **kwargs) -> dict:
        """Investiga un tema: descompone, busca fuentes, sintetiza."""
        params: dict = {"question": question}
        params.update(kwargs)
        result = await self._session.call_tool("research", params)
        return _parse_tool_result(result)

    async def find_similar(self, url: str, **kwargs) -> dict:
        """Encuentra paginas web similares a una URL dada usando fusion keyword+embedding+web."""
        params: dict = {"url": url}
        params.update(kwargs)
        result = await self._session.call_tool("find_similar", params)
        return _parse_tool_result(result)

    async def agent(self, task: str, **kwargs) -> dict:
        """Agente autonomo de busqueda: plan -> search -> fetch -> sintetiza."""
        params: dict = {"task": task}
        params.update(kwargs)
        result = await self._session.call_tool("agent", params)
        return _parse_tool_result(result)


# ============================================================
# OpenSEO MCP Client (HTTP, self-hosted)
# ============================================================

@asynccontextmanager
async def openseo_session() -> AsyncIterator[ClientSession]:
    """Conecta a OpenSEO via HTTP (Docker self-hosted)."""
    async with streamablehttp_client(config.openseo.mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            logger.info("OpenSEO MCP conectado")
            yield session


class OpenSEOClient:
    """Wrapper tipado sobre las tools MCP de OpenSEO."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def research_keywords(
        self, keywords: list[str], *, location_code: int = 2840, **kwargs
    ) -> dict:
        """Investiga keywords: volumen, dificultad, CPC, SERP features."""
        params: dict = {"keywords": keywords, "location_code": location_code}
        params.update(kwargs)
        result = await self._session.call_tool("research-keywords", params)
        return _parse_tool_result(result)

    async def get_domain_overview(self, domain: str, **kwargs) -> dict:
        """Trafico estimado, top keywords, datos del dominio."""
        params: dict = {"domain": domain}
        params.update(kwargs)
        result = await self._session.call_tool("get-domain-overview", params)
        return _parse_tool_result(result)

    async def get_domain_keyword_suggestions(
        self, domain: str, **kwargs
    ) -> dict:
        """Sugerencias de keywords para un dominio."""
        params: dict = {"domain": domain}
        params.update(kwargs)
        result = await self._session.call_tool("get-domain-keyword-suggestions", params)
        return _parse_tool_result(result)

    async def get_backlinks_overview(self, domain: str, **kwargs) -> dict:
        """Resumen de perfil de backlinks."""
        params: dict = {"target": domain}
        params.update(kwargs)
        result = await self._session.call_tool("get-backlinks-overview", params)
        return _parse_tool_result(result)

    async def get_backlinks_profile(self, domain: str, **kwargs) -> dict:
        """Perfil detallado de backlinks."""
        params: dict = {"target": domain}
        params.update(kwargs)
        result = await self._session.call_tool("get-backlinks-profile", params)
        return _parse_tool_result(result)

    async def get_serp_results(
        self, keyword: str, *, location_code: int = 2840, **kwargs
    ) -> dict:
        """Resultados SERP para una keyword."""
        params: dict = {"keyword": keyword, "location_code": location_code}
        params.update(kwargs)
        result = await self._session.call_tool("get-serp-results", params)
        return _parse_tool_result(result)

    async def get_rank_tracker(self, project_id: str, **kwargs) -> dict:
        """Datos de rank tracking para un proyecto."""
        params: dict = {"project_id": project_id}
        params.update(kwargs)
        result = await self._session.call_tool("get-rank-tracker", params)
        return _parse_tool_result(result)

    async def list_saved_keywords(self, project_id: str, **kwargs) -> dict:
        """Keywords guardadas en un proyecto."""
        params: dict = {"project_id": project_id}
        params.update(kwargs)
        result = await self._session.call_tool("list-saved-keywords", params)
        return _parse_tool_result(result)

    async def save_keywords(
        self, project_id: str, keywords: list[dict], **kwargs
    ) -> dict:
        """Guarda keywords en un proyecto."""
        params: dict = {"project_id": project_id, "keywords": keywords}
        params.update(kwargs)
        result = await self._session.call_tool("save-keywords", params)
        return _parse_tool_result(result)


# ============================================================
# Helpers
# ============================================================

def _parse_tool_result(result) -> dict:
    """Extrae el contenido util de un CallToolResult de MCP."""
    if result.isError:
        raise RuntimeError(f"MCP tool error: {result.content}")

    # result.content es una lista de ContentBlock (text/image/resource)
    for block in result.content:
        if hasattr(block, "text"):
            try:
                return json.loads(block.text)
            except Exception:
                return {"text": block.text}

    return {"raw": str(result.content)}

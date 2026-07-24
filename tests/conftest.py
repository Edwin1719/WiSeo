"""Fixtures compartidos para los tests del SEO Agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ============================================================
# MCP CallToolResult helpers
# ============================================================

def make_mcp_result(text: str, *, is_error: bool = False) -> MagicMock:
    """Crea un CallToolResult simulado de MCP con un text block."""
    result = MagicMock()
    result.isError = is_error
    block = MagicMock()
    block.text = text
    result.content = [block]
    return result


def make_mcp_result_non_json(text: str) -> MagicMock:
    """Crea un CallToolResult con texto no-JSON."""
    return make_mcp_result(text)


def make_mcp_result_no_text() -> MagicMock:
    """Crea un CallToolResult sin text blocks."""
    result = MagicMock()
    result.isError = False
    result.content = [MagicMock(spec=[])]  # objeto sin atributo .text
    return result


# ============================================================
# Mock MCP Clients
# ============================================================

@pytest.fixture
def mock_wigolo() -> AsyncMock:
    """Mock del WigoloClient con todas las tools como AsyncMock."""
    client = AsyncMock()
    client.search = AsyncMock()
    client.fetch = AsyncMock()
    client.extract = AsyncMock()
    client.crawl = AsyncMock()
    client.research = AsyncMock()
    client.find_similar = AsyncMock()
    return client


@pytest.fixture
def mock_openseo() -> AsyncMock:
    """Mock del OpenSEOClient con todas las tools como AsyncMock."""
    client = AsyncMock()
    client.research_keywords = AsyncMock()
    client.get_domain_overview = AsyncMock()
    client.get_serp_results = AsyncMock()
    client.get_backlinks_overview = AsyncMock()
    return client

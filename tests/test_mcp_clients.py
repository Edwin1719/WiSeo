"""Tests para src.mcp.clients — _parse_tool_result (hotspot fan-in 15)."""

from __future__ import annotations

import pytest

from src.mcp.clients import _parse_tool_result


class TestParseToolResult:
    """_parse_tool_result es invocada por todas las tools MCP (fan-in 15).

    Cubre: 4 formatos de respuesta MCP + 1 caso de error.
    """

    def test_json_text_block(self):
        """Texto JSON → dict parseado."""
        result = _parse_tool_result(
            _make_mcp_result('{"key": "value", "number": 42}', is_error=False)
        )
        assert result == {"key": "value", "number": 42}

    def test_non_json_text_block(self):
        """Texto no-JSON → {"text": ...}."""
        result = _parse_tool_result(
            _make_mcp_result("respuesta plana sin json", is_error=False)
        )
        assert result == {"text": "respuesta plana sin json"}

    def test_nested_json(self):
        """JSON anidado con listas."""
        data = {
            "results": [
                {"keyword": "seo", "volume": 1200},
                {"keyword": "marketing", "volume": 3400},
            ],
            "total": 2,
        }
        result = _parse_tool_result(
            _make_mcp_result('{"results": [{"keyword": "seo", "volume": 1200}, {"keyword": "marketing", "volume": 3400}], "total": 2}', is_error=False)
        )
        assert result == data

    def test_no_text_block(self):
        """Sin text blocks → {"raw": ...}."""
        mock = _make_mcp_no_text()
        result = _parse_tool_result(mock)
        assert "raw" in result

    def test_error_flag_raises(self):
        """isError=True → RuntimeError."""
        mock = _make_mcp_result("error msg", is_error=True)
        with pytest.raises(RuntimeError, match="MCP tool error"):
            _parse_tool_result(mock)

    def test_first_text_block_wins(self):
        """Si hay multiples text blocks, usa el primero."""
        from unittest.mock import MagicMock

        mock = MagicMock()
        mock.isError = False
        block1 = MagicMock()
        block1.text = '{"source": "first"}'
        block2 = MagicMock()
        block2.text = '{"source": "second"}'
        mock.content = [block1, block2]

        result = _parse_tool_result(mock)
        assert result == {"source": "first"}


# ============================================================
# Helpers locales (evitan depender de conftest para tests simples)
# ============================================================

from unittest.mock import MagicMock


def _make_mcp_result(text: str, *, is_error: bool = False) -> MagicMock:
    """Crea un CallToolResult simulado de MCP."""
    result = MagicMock()
    result.isError = is_error
    block = MagicMock()
    block.text = text
    result.content = [block]
    return result


def _make_mcp_no_text() -> MagicMock:
    """Crea un CallToolResult sin text blocks."""
    result = MagicMock()
    result.isError = False
    result.content = [MagicMock(spec=[])]
    return result

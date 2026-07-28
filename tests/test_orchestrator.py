"""Tests para src.agent.orchestrator.

Cubre:
  - ToolExecutor: dispatch, error handling, _check_ai_overview, _validate_sitemaps
  - SEOAgent: state management (add_message, reset, history, tool_calls_log)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.orchestrator import SEOAgent, ToolExecutor, ToolResult


# ============================================================
# ToolExecutor — dispatch
# ============================================================

class TestToolExecutorDispatch:
    """Enrutamiento de tool names a handlers."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, mock_wigolo, mock_openseo):
        """Tool name no registrado → error descriptivo."""
        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute("tool_inexistente", "{}", "call_1")
        assert isinstance(result, ToolResult)
        parsed = json.loads(result.content)
        assert "error" in parsed
        assert "tool_inexistente" in parsed["error"]

    @pytest.mark.asyncio
    async def test_invalid_json_args_returns_error(self, mock_wigolo, mock_openseo):
        """Argumentos JSON invalidos → error capturado."""
        executor = ToolExecutor(mock_wigolo, mock_openseo)
        # Registrar un handler simple para probar
        executor._handlers["test_echo"] = lambda msg="": msg
        result = await executor.execute("test_echo", "no-es-json", "call_1")
        parsed = json.loads(result.content)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_handler_exception_caught(self, mock_wigolo, mock_openseo):
        """Excepcion en handler → error en content, no crash."""
        async def _failing(*args, **kwargs):
            raise ValueError("algo salio mal")

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        executor._handlers["test_fail"] = _failing
        result = await executor.execute("test_fail", "{}", "call_1")
        parsed = json.loads(result.content)
        assert "error" in parsed
        assert "algo salio mal" in parsed["error"]

    @pytest.mark.asyncio
    async def test_handler_result_serializable(self, mock_wigolo, mock_openseo):
        """Resultado del handler se serializa a JSON correctamente."""
        async def _handler(url: str = ""):
            return {"url": url, "status": "ok"}

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        executor._handlers["test_ok"] = _handler
        result = await executor.execute(
            "test_ok", '{"url": "https://ejemplo.com"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert parsed == {"url": "https://ejemplo.com", "status": "ok"}


# ============================================================
# ToolExecutor — _check_ai_overview
# ============================================================

class TestCheckAIIOverview:
    """Logica de deteccion de AI Overview."""

    @pytest.mark.asyncio
    async def test_detects_ai_overview(self, mock_wigolo, mock_openseo):
        """Detecta AI Overview cuando la busqueda contiene indicadores."""
        mock_wigolo.search.return_value = {
            "text": (
                "Resultados de busqueda: AI Overview generado por inteligencia "
                "artificial muestra un resumen en la parte superior"
            ),
            "results": [
                {"url": "https://example.com/fuente-1"},
                {"url": "https://example.com/fuente-2"},
            ],
        }
        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "seo_ai_overview", '{"keyword": "beneficios seo"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert parsed["keyword"] == "beneficios seo"
        assert parsed["has_ai_overview"] is True
        assert len(parsed["indicators_found"]) > 0
        assert len(parsed["sources"]) > 0

    @pytest.mark.asyncio
    async def test_no_ai_overview(self, mock_wigolo, mock_openseo):
        """No detecta AI Overview cuando no hay indicadores."""
        mock_wigolo.search.return_value = {
            "results": [
                {"url": "https://example.com/resultado-normal"},
            ],
        }
        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "seo_ai_overview", '{"keyword": "noticias deportivas"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert parsed["has_ai_overview"] is False
        assert parsed["indicators_found"] == []

    @pytest.mark.asyncio
    async def test_search_error_returns_error(self, mock_wigolo, mock_openseo):
        """Error en la busqueda → error en resultado."""
        mock_wigolo.search.side_effect = RuntimeError("Wigolo no disponible")
        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "seo_ai_overview", '{"keyword": "test"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert "error" in parsed


# ============================================================
# ToolExecutor — _validate_sitemaps
# ============================================================

class TestValidateSitemaps:
    """Validacion de robots.txt + sitemaps XML."""

    @pytest.mark.asyncio
    async def test_robots_txt_and_sitemap_ok(self, mock_wigolo, mock_openseo):
        """robots.txt 200 + sitemap XML valido."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            # robots.txt response
            robots_resp = MagicMock()
            robots_resp.status_code = 200
            robots_resp.text = (
                "User-agent: *\n"
                "Disallow: /admin/\n"
                "Sitemap: https://example.com/sitemap.xml\n"
                "Crawl-delay: 10\n"
            )

            # sitemap response
            sitemap_resp = MagicMock()
            sitemap_resp.status_code = 200
            sitemap_resp.content = (
                b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                b"<url><loc>https://example.com/</loc></url>"
                b"<url><loc>https://example.com/blog</loc></url>"
                b"<url><loc>https://example.com/about</loc></url>"
                b"</urlset>"
            )

            mock_client.get.side_effect = [robots_resp, sitemap_resp]

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "seo_validate_sitemaps",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            assert parsed["url"] == "https://example.com"
            assert parsed["robots_txt"]["status"] == "ok"
            assert len(parsed["sitemaps"]) == 1
            assert parsed["sitemaps"][0]["total_urls"] == 3

    @pytest.mark.asyncio
    async def test_robots_txt_404(self, mock_wigolo, mock_openseo):
        """robots.txt 404 → warning y sin sitemaps."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            robots_resp = MagicMock()
            robots_resp.status_code = 404
            robots_resp.text = "Not Found"
            mock_client.get.return_value = robots_resp

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "seo_validate_sitemaps",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            assert parsed["robots_txt"]["status"] == "missing"
            assert any("404" in issue["msg"] for issue in parsed["issues"])

    @pytest.mark.asyncio
    async def test_disallow_conflict_warning(self, mock_wigolo, mock_openseo):
        """Disallow rules + sitemap presente → warning."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            robots_resp = MagicMock()
            robots_resp.status_code = 200
            robots_resp.text = (
                "User-agent: *\n"
                "Disallow: /private/\n"
                "Disallow: /temp/\n"
                "Sitemap: https://example.com/sitemap.xml\n"
            )

            sitemap_resp = MagicMock()
            sitemap_resp.status_code = 200
            sitemap_resp.content = (
                b'<?xml version="1.0"?>'
                b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                b"<url><loc>https://example.com/</loc></url>"
                b"</urlset>"
            )

            mock_client.get.side_effect = [robots_resp, sitemap_resp]

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "seo_validate_sitemaps",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            disallow_warnings = [
                i for i in parsed["issues"]
                if "Disallow" in i.get("msg", "")
            ]
            assert len(disallow_warnings) >= 1

    @pytest.mark.asyncio
    async def test_no_sitemaps_found(self, mock_wigolo, mock_openseo):
        """Sin sitemaps accesibles → warning."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            robots_resp = MagicMock()
            robots_resp.status_code = 200
            robots_resp.text = "User-agent: *\nDisallow: /admin/\n"

            not_found = MagicMock()
            not_found.status_code = 404

            mock_client.get.side_effect = [robots_resp, not_found]

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "seo_validate_sitemaps",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            assert parsed["sitemaps"] == []
            no_sitemap_warnings = [
                i for i in parsed["issues"]
                if "sitemaps" in i.get("msg", "").lower()
            ]
            assert len(no_sitemap_warnings) >= 1


# ============================================================
# SEOAgent — state management
# ============================================================

class TestSEOAgentState:
    """Gestion del estado interno del agente."""

    @pytest.mark.asyncio
    async def test_add_message(self, mock_wigolo, mock_openseo):
        """add_message() agrega al historial."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        agent.add_message("user", "Hola")
        assert len(agent.history) == 1
        assert agent.history[0] == {"role": "user", "content": "Hola"}

    @pytest.mark.asyncio
    async def test_add_multiple_messages(self, mock_wigolo, mock_openseo):
        """Mensajes se acumulan en orden."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        agent.add_message("user", "M1")
        agent.add_message("assistant", "R1")
        agent.add_message("user", "M2")
        assert len(agent.history) == 3
        assert [m["role"] for m in agent.history] == ["user", "assistant", "user"]

    @pytest.mark.asyncio
    async def test_reset_clears_history(self, mock_wigolo, mock_openseo):
        """reset() limpia historial pero mantiene system prompt."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        agent.add_message("user", "M1")
        agent.add_message("assistant", "R1")
        agent.reset()
        assert agent.history == []  # system prompt no se cuenta en .history
        # Confirmar que el system prompt interno sigue vivo
        agent.add_message("user", "nueva")
        assert len(agent.history) == 1

    @pytest.mark.asyncio
    async def test_reset_clears_tool_log(self, mock_wigolo, mock_openseo):
        """reset() tambien limpia tool_calls_log."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        agent._tool_calls_log.append({"name": "test", "arguments": "{}", "ts": 0})
        agent.reset()
        assert agent.tool_calls_log == []

    @pytest.mark.asyncio
    async def test_tool_calls_log_accessible(self, mock_wigolo, mock_openseo):
        """tool_calls_log property devuelve la lista."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        assert agent.tool_calls_log == []
        agent._tool_calls_log.append({"name": "search", "arguments": "{}", "ts": 0})
        assert len(agent.tool_calls_log) == 1
        assert agent.tool_calls_log[0]["name"] == "search"

    @pytest.mark.asyncio
    async def test_history_excludes_system_prompt(self, mock_wigolo, mock_openseo):
        """.history no incluye el system prompt."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        assert agent.history == []
        # El primer mensaje deberia ser el primero del usuario
        agent.add_message("user", "consulta")
        assert agent.history[0]["role"] == "user"


# ============================================================
# _extract_seo_stats
# ============================================================

class TestExtractSEOStats:
    """Extraccion de estadisticas del dashboard desde tool_calls_log."""

    def _build_agent(self, tool_calls: list[dict], mock_wigolo, mock_openseo):
        """Helper: crea agente con tool_calls_log pre-poblado."""
        agent = SEOAgent(mock_wigolo, mock_openseo)
        for tc in tool_calls:
            agent._tool_calls_log.append(tc)
        return agent

    @pytest.mark.asyncio
    async def test_extracts_keywords(self, mock_wigolo, mock_openseo):
        """Extrae keywords desde openseo_research_keywords."""
        agent = self._build_agent(
            [
                {
                    "name": "openseo_research_keywords",
                    "arguments": '{"keywords": ["seo", "marketing"]}',
                    "ts": 0,
                },
            ],
            mock_wigolo,
            mock_openseo,
        )
        from streamlit_app import _extract_seo_stats

        # Simular session_state minimo
        import streamlit as st

        st.session_state.agent = agent
        st.session_state.seo_stats = {
            "keywords": [],
            "domains": [],
            "serps": [],
            "pagespeed": [],
            "tool_count": 0,
        }
        _extract_seo_stats()
        assert "seo" in st.session_state.seo_stats["keywords"]
        assert "marketing" in st.session_state.seo_stats["keywords"]

    @pytest.mark.asyncio
    async def test_extracts_domains(self, mock_wigolo, mock_openseo):
        """Extrae dominios desde openseo_domain_overview."""
        agent = self._build_agent(
            [
                {
                    "name": "openseo_domain_overview",
                    "arguments": '{"domain": "example.com"}',
                    "ts": 0,
                },
            ],
            mock_wigolo,
            mock_openseo,
        )
        import streamlit as st

        st.session_state.agent = agent
        st.session_state.seo_stats = {
            "keywords": [],
            "domains": [],
            "serps": [],
            "pagespeed": [],
            "tool_count": 0,
        }
        from streamlit_app import _extract_seo_stats

        _extract_seo_stats()
        assert "example.com" in st.session_state.seo_stats["domains"]


# ============================================================
# ToolExecutor — _validate_llms_txt
# ============================================================

class TestValidateLlmstxt:
    """Validacion de llms.txt para AI crawlers."""

    @pytest.mark.asyncio
    async def test_llms_txt_ok(self, mock_wigolo, mock_openseo):
        """llms.txt valido con secciones y URLs."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            resp = MagicMock()
            resp.status_code = 200
            resp.text = (
                "## Docs\n"
                "- [Guia SEO](https://example.com/guia-seo)\n"
                "- [API Ref](https://example.com/api)\n\n"
                "## Blog\n"
                "- [SEO 2026](https://example.com/blog/seo-2026)\n"
            )
            mock_client.get.return_value = resp

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "geo_llms_txt",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            assert parsed["exists"] is True
            assert parsed["urls_found"] == 3
            assert "Docs" in parsed["sections"]
            assert "Blog" in parsed["sections"]

    @pytest.mark.asyncio
    async def test_llms_txt_404(self, mock_wigolo, mock_openseo):
        """Dominio sin llms.txt → warning."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            resp = MagicMock()
            resp.status_code = 404
            mock_client.get.return_value = resp

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "geo_llms_txt",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            assert parsed["exists"] is False
            assert any("404" in i["msg"] for i in parsed["issues"])

    @pytest.mark.asyncio
    async def test_llms_txt_no_sections(self, mock_wigolo, mock_openseo):
        """llms.txt existe pero sin estructura → suggestions."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client_cls.return_value = mock_client

            resp = MagicMock()
            resp.status_code = 200
            resp.text = "- [Home](https://example.com)\n- [About](https://example.com/about)\n"
            mock_client.get.return_value = resp

            executor = ToolExecutor(mock_wigolo, mock_openseo)
            result = await executor.execute(
                "geo_llms_txt",
                '{"url": "https://example.com"}',
                "call_1",
            )
            parsed = json.loads(result.content)
            assert parsed["exists"] is True
            assert parsed["urls_found"] == 2
            assert not parsed["sections"]  # sin ## headings
            assert any("Sin secciones" in i["msg"] for i in parsed["issues"])


# ============================================================
# ToolExecutor — _check_geo_citations
# ============================================================

class TestCheckGeoCitations:
    """Deteccion de citas de marca en plataformas de IA."""

    @pytest.mark.asyncio
    async def test_all_platforms_cited(self, mock_wigolo, mock_openseo):
        """Marca aparece en todas las plataformas → score 100."""
        mock_wigolo.search = AsyncMock(return_value="Databiq es una plataforma lider en BI...")

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_citation_check",
            '{"brand": "Databiq"}',
            "call_1",
        )
        parsed = json.loads(result.content)
        assert parsed["citation_score"] == 100
        assert parsed["platforms_cited"] == 6
        assert parsed["platforms_total"] == 6

    @pytest.mark.asyncio
    async def test_no_platforms_cited(self, mock_wigolo, mock_openseo):
        """Marca desconocida → score 0."""
        mock_wigolo.search = AsyncMock(return_value="Sin resultados relevantes.")

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_citation_check",
            '{"brand": "XyzMarcaInventada123"}',
            "call_1",
        )
        parsed = json.loads(result.content)
        assert parsed["citation_score"] == 0
        assert parsed["platforms_cited"] == 0

    @pytest.mark.asyncio
    async def test_search_error_graceful(self, mock_wigolo, mock_openseo):
        """Fallo en busqueda → cited=False, no interrumpe el resto."""
        mock_wigolo.search = AsyncMock(side_effect=Exception("Timeout"))

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_citation_check",
            '{"brand": "Databiq"}',
            "call_1",
        )
        parsed = json.loads(result.content)
        assert parsed["citation_score"] == 0
        assert parsed["platforms_cited"] == 0
        assert parsed["platforms_total"] == 6  # no se rompe


# ============================================================
# ToolExecutor — _audit_geo_content
# ============================================================

class TestAuditGeoContent:
    """Auditoria GEO de contenido contra 5 senales."""

    @pytest.mark.asyncio
    async def test_excellent_content(self, mock_wigolo, mock_openseo):
        """Contenido optimizado → score alto."""
        mock_wigolo.fetch = AsyncMock(return_value=(
            "# Business Intelligence para Empresas\n\n"
            "En 2024, el 67% de empresas adoptaron BI segun "
            "[estudio de Gartner](https://doi.org/10.1234/bi2024). "
            "La tasa crecio un 23.5% respecto al 2023. "
            "Segun [Wikipedia](https://en.wikipedia.org/wiki/BI), "
            "el mercado alcanzara $40 mil millones en 2025.\n\n"
            "## Beneficios\n\n"
            "### Reduccion de costos\n\n"
            "Las empresas reportan ahorros del 30%.\n\n"
            "### Toma de decisiones\n\n"
            "Decisiones basadas en datos.\n\n"
            "## Casos de exito\n\n"
            "[Netflix](https://netflix.com) y [Amazon](https://amazon.com) usan BI."
        ))
        mock_wigolo.extract = AsyncMock(return_value=(
            '{"schema.org": "Article", "ld+json": true,'
            '"og:title": "BI para Empresas"}'
        ))
        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_content_audit", '{"url": "https://example.com/articulo"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert parsed["geo_score"] >= 75
        assert parsed["signals"]["structured_data"] == 25
        assert parsed["signals"]["stats_and_sources"] == 25
        assert len(parsed["recommendations"]) <= 2

    @pytest.mark.asyncio
    async def test_thin_content(self, mock_wigolo, mock_openseo):
        """Contenido pobre → score bajo + recomendaciones."""
        mock_wigolo.fetch = AsyncMock(return_value=(
            "# Bienvenidos\n\nSomos una empresa de datos.\n\n"
            "## Servicios\n\nOfrecemos analisis y consultoria.\n\n"
            "Contactanos para mas informacion."
        ))
        mock_wigolo.extract = AsyncMock(return_value="{}")

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_content_audit", '{"url": "https://example.com/pobre"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert parsed["geo_score"] <= 30
        assert parsed["signals"]["structured_data"] == 0
        assert len(parsed["recommendations"]) >= 2

    @pytest.mark.asyncio
    async def test_fetch_error_graceful(self, mock_wigolo, mock_openseo):
        """Fallo en fetch → score 0 sin romper."""
        mock_wigolo.fetch = AsyncMock(side_effect=Exception("Timeout"))
        mock_wigolo.extract = AsyncMock(side_effect=Exception("Timeout"))

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_content_audit", '{"url": "https://example.com"}', "call_1"
        )
        parsed = json.loads(result.content)
        assert parsed["geo_score"] == 0
        assert len(parsed["recommendations"]) >= 1


# ============================================================
# ToolExecutor — _check_geo_share_of_voice
# ============================================================

class TestGeoShareOfVoice:
    """Share of Voice competitivo en plataformas de IA."""

    @pytest.mark.asyncio
    async def test_brand_leads(self, mock_wigolo, mock_openseo):
        """Marca lidera sobre competidores."""
        mock_wigolo.search = AsyncMock(side_effect=lambda q, **kw: (
            "Databiq es lider en BI..." if "Databiq" in q else "Sin resultados"
        ))

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_share_of_voice",
            '{"brand": "Databiq", "competitors": ["IBM", "AWS"]}',
            "call_1",
        )
        parsed = json.loads(result.content)
        assert parsed["leader"] == "Databiq"
        assert parsed["share_of_voice"]["Databiq"] == 100
        assert parsed["share_of_voice"]["IBM"] == 0

    @pytest.mark.asyncio
    async def test_competitor_dominates(self, mock_wigolo, mock_openseo):
        """Competidor externo lidera, marca atras."""
        def search_side_effect(query, max_results=5):
            if "Databiq" in query:
                return "Sin resultados"
            return "Google Cloud plataforma lider de BI y analitica de datos"

        mock_wigolo.search = AsyncMock(side_effect=search_side_effect)

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_share_of_voice",
            '{"brand": "Databiq", "competitors": ["Google Cloud"]}',
            "call_1",
        )
        parsed = json.loads(result.content)
        assert parsed["leader"] == "Google Cloud"
        assert parsed["share_of_voice"]["Databiq"] == 0

    @pytest.mark.asyncio
    async def test_all_zero(self, mock_wigolo, mock_openseo):
        """Ninguna marca es citada → todos 0%."""
        mock_wigolo.search = AsyncMock(return_value="Sin resultados relevantes")

        executor = ToolExecutor(mock_wigolo, mock_openseo)
        result = await executor.execute(
            "geo_share_of_voice",
            '{"brand": "Xyz", "competitors": ["Abc", "Def"]}',
            "call_1",
        )
        parsed = json.loads(result.content)
        for b in ["Xyz", "Abc", "Def"]:
            assert parsed["share_of_voice"][b] == 0

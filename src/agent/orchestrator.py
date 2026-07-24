"""
Orquestador del agente SEO — conecta DeepSeek con los MCP clients.

Flujo:
  1. Recibe mensaje del usuario
  2. DeepSeek decide si necesita tools
  3. Si necesita → ejecuta tool → reenvia resultado al LLM
  4. Repite hasta que el LLM produce una respuesta final
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

import httpx
from openai import AsyncOpenAI

from src.mcp.clients import OpenSEOClient, WigoloClient
from src.utils.config import config

logger = logging.getLogger(__name__)


# ============================================================
# Tool Registry — Define que tools puede usar el LLM
# ============================================================

WIGOLO_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "wigolo_search",
            "description": "Busca en la web usando multiples motores de busqueda en paralelo. Usa esto para investigar SERPs, encontrar competidores, buscar oportunidades de guest posting, o encontrar informacion actualizada sobre cualquier tema SEO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Query de busqueda, o array de queries para busqueda paralela.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximo de resultados. Default: 10.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wigolo_fetch",
            "description": "Carga y extrae el contenido de una URL en formato markdown. Util para analizar paginas de competidores, extraer estructuras de contenido, o leer articulos completos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL a cargar."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wigolo_extract",
            "description": "Extrae datos estructurados de una pagina: headings, metadata, JSON-LD, tablas, schema markup, o schemas personalizados. Usa esto para analizar la estructura SEO on-page de una URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL a analizar."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wigolo_crawl",
            "description": "Crawlea multiples paginas de un sitio (BFS/DFS/sitemap). Util para mapear la arquitectura completa del sitio de un competidor o analizar la estructura de internal linking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL raiz del sitio a crawlear."},
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximo de paginas a crawlear. Default: 20.",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wigolo_research",
            "description": "Investiga un tema a fondo: descompone la pregunta, busca en multiples fuentes, y sintetiza un reporte con citas. Para analisis de mercado, tendencias, o investigacion competitiva profunda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Pregunta o tema a investigar.",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wigolo_find_similar",
            "description": "Encuentra paginas web tematicamente similares a una URL dada. Util para descubrir competidores organicos, oportunidades de guest posting, prospeccion de link building, o encontrar sitios alternativos en el mismo nicho SEO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL de referencia para buscar similares (ej. https://databiq.com).",
                    },
                },
                "required": ["url"],
            },
        },
    },
]

OPENSEO_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "openseo_research_keywords",
            "description": "Investiga keywords en DataForSEO: obtiene volumen de busqueda mensual, dificultad, CPC, competencia, y SERP features. Usa esto cuando necesites datos CUANTITATIVOS de keywords (volumen exacto, dificultad, CPC).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de keywords a investigar.",
                    },
                    "location_code": {
                        "type": "integer",
                        "description": "Codigo de ubicacion. 2840 = USA. Default: 2840.",
                    },
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_domain_overview",
            "description": "Analiza un dominio: trafico organico estimado, top keywords, posicion promedio, trafico pagado. Usa esto para analizar competidores o diagnosticar un dominio propio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Dominio a analizar (ej. 'nike.com').",
                    },
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_serp_results",
            "description": "Obtiene los resultados actuales del SERP para una keyword: quien rankea, en que posicion, con que titulo/descripcion, y que SERP features aparecen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Keyword a consultar."},
                    "location_code": {
                        "type": "integer",
                        "description": "Codigo de ubicacion. Default: 2840 (USA).",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_backlinks_overview",
            "description": "Resumen del perfil de backlinks de un dominio: total de backlinks, dominios de referencia, anchor texts mas comunes, y distribucion por tipo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Dominio a analizar backlinks.",
                    },
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_domain_keyword_suggestions",
            "description": "Sugiere keywords relacionadas a un dominio. Util para descubrir nuevos topicos y oportunidades de contenido basadas en el perfil de keywords de un competidor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Dominio para obtener sugerencias de keywords (ej. 'nike.com').",
                    },
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_backlinks_profile",
            "description": "Perfil detallado de backlinks de un dominio: paginas de referencia, anchor texts, tipos de enlace, distribucion por autoridad. Mas profundo que el resumen basico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Dominio a analizar perfil detallado de backlinks.",
                    },
                },
                "required": ["domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_rank_tracker",
            "description": "Obtiene el historico de posiciones de keywords en un proyecto de rank tracking. Util para monitorear la evolucion del ranking de keywords a lo largo del tiempo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID del proyecto de rank tracking en DataForSEO.",
                    },
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_list_saved_keywords",
            "description": "Lista las keywords guardadas en un proyecto de DataForSEO. Util para revisar keywords previamente investigadas y su estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID del proyecto en DataForSEO.",
                    },
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "openseo_save_keywords",
            "description": "Guarda keywords en un proyecto de DataForSEO para seguimiento y rank tracking futuro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID del proyecto en DataForSEO.",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de keywords a guardar.",
                    },
                },
                "required": ["project_id", "keywords"],
            },
        },
    },
]

PAGESPEED_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "pagespeed_analyze",
            "description": "Analiza la velocidad y Core Web Vitals de una URL usando Google PageSpeed Insights. Devuelve puntuacion (0-100), LCP, CLS, INP, TTFB, FCP, y recomendaciones de mejora. Usa esto para diagnosticar rendimiento web de cualquier sitio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL completa a analizar (ej. https://databiq.com).",
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["mobile", "desktop"],
                        "description": "Estrategia de analisis: mobile o desktop. Default: mobile.",
                    },
                },
                "required": ["url"],
            },
        },
    },
]

ALL_TOOLS: list[dict[str, Any]] = WIGOLO_TOOLS + OPENSEO_TOOLS + PAGESPEED_TOOLS + [
    {
        "type": "function",
        "function": {
            "name": "seo_validate_sitemaps",
            "description": "Valida robots.txt y sitemaps XML de un sitio web. Detecta: directivas de robots.txt, URLs en sitemap vs bloqueadas por robots.txt, errores de estructura XML, URLs rotas, y conflictos de indexacion. Util para diagnosticar problemas de indexacion en cualquier dominio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL raiz del sitio (ej. https://databiq.com). Se analizaran /robots.txt y /sitemap.xml.",
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "seo_ai_overview",
            "description": "Verifica si una keyword activa AI Overview (antes SGE) en Google. Busca informacion y detecta si el resultado de busqueda contiene respuestas generadas por inteligencia artificial. Util para saber si una keyword tiene AI Overview y que fuentes cita.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword a verificar (ej. 'beneficios del SEO').",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
]


# ============================================================
# Tool executor — Mapea function_name → llamada real al MCP
# ============================================================

@dataclass
class ToolResult:
    """Resultado de ejecutar una tool MCP, listo para volver al LLM."""

    role: str = "tool"
    tool_call_id: str = ""
    content: str = ""


class ToolExecutor:
    """Ejecuta tools MCP y devuelve resultados formateados para el LLM."""

    def __init__(self, wigolo: WigoloClient, openseo: OpenSEOClient) -> None:
        self._wigolo = wigolo
        self._openseo = openseo
        self._handlers: dict[str, Any] = {
            "wigolo_search": self._wigolo.search,
            "wigolo_fetch": self._wigolo.fetch,
            "wigolo_extract": self._wigolo.extract,
            "wigolo_crawl": self._wigolo.crawl,
            "wigolo_research": self._wigolo.research,
            "wigolo_find_similar": self._wigolo.find_similar,
            "openseo_research_keywords": self._openseo.research_keywords,
            "openseo_domain_overview": self._openseo.get_domain_overview,
            "openseo_serp_results": self._openseo.get_serp_results,
            "openseo_backlinks_overview": self._openseo.get_backlinks_overview,
            "openseo_domain_keyword_suggestions": self._openseo.get_domain_keyword_suggestions,
            "openseo_backlinks_profile": self._openseo.get_backlinks_profile,
            "openseo_rank_tracker": self._openseo.get_rank_tracker,
            "openseo_list_saved_keywords": self._openseo.list_saved_keywords,
            "openseo_save_keywords": self._openseo.save_keywords,
            "pagespeed_analyze": self._pagespeed_analyze,
            "seo_validate_sitemaps": self._validate_sitemaps,
            "seo_ai_overview": self._check_ai_overview,
        }

    async def _pagespeed_analyze(self, url: str, strategy: str = "mobile") -> dict:
        """Llama a Google PageSpeed Insights API y devuelve metricas estructuradas."""
        api_key = config.pagespeed.api_key
        if not api_key:
            return {"error": "GOOGLE_PAGESPEED_API_KEY no configurada en .env"}

        params = {"url": url, "strategy": strategy, "key": api_key}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(config.pagespeed.base_url, params=params)
            data = resp.json()

        if "error" in data:
            return {"error": data["error"].get("message", "Error desconocido de PageSpeed")}

        lh = data.get("lighthouseResult", {})
        audits = lh.get("audits", {})
        categories = lh.get("categories", {})

        # Extraer metricas clave
        score = categories.get("performance", {}).get("score", 0)
        if score is not None:
            score = round(score * 100)

        def _metric(key: str) -> str | None:
            a = audits.get(key)
            return a.get("displayValue") if a else None

        return {
            "url": url,
            "strategy": strategy,
            "score": score,
            "lcp": _metric("largest-contentful-paint"),
            "cls": _metric("cumulative-layout-shift"),
            "inp": _metric("interaction-to-next-paint"),
            "ttfb": _metric("server-response-time"),
            "fcp": _metric("first-contentful-paint"),
            "si": _metric("speed-index"),
            "title": lh.get("finalDisplayedUrl", url),
            "lighthouse_version": lh.get("lighthouseVersion", ""),
        }

    async def _validate_sitemaps(self, url: str) -> dict:
        """Valida robots.txt y sitemaps XML de un sitio."""
        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        result = {"url": root, "robots_txt": {}, "sitemaps": [], "issues": []}

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # 1. Obtener robots.txt
            try:
                resp = await client.get(f"{root}/robots.txt")
                if resp.status_code == 200:
                    lines = resp.text.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line.lower().startswith(("user-agent", "disallow", "allow", "sitemap", "crawl-delay")):
                            key, _, val = line.partition(":")
                            result["robots_txt"][key.strip()] = val.strip()
                    result["robots_txt"]["status"] = "ok"
                elif resp.status_code == 404:
                    result["issues"].append({"type": "warning", "msg": "No se encuentra robots.txt (HTTP 404)"})
                    result["robots_txt"]["status"] = "missing"
                else:
                    result["issues"].append({"type": "error", "msg": f"robots.txt respondio HTTP {resp.status_code}"})
                    result["robots_txt"]["status"] = f"http_{resp.status_code}"
            except Exception as exc:
                result["issues"].append({"type": "error", "msg": f"Error al obtener robots.txt: {exc}"})

            # 2. Buscar sitemaps (desde robots.txt o ruta por defecto)
            sitemap_urls = []
            sm_directive = result["robots_txt"].get("Sitemap")
            if sm_directive:
                sitemap_urls.append(sm_directive)
            sitemap_urls.append(f"{root}/sitemap.xml")

            for sm_url in sitemap_urls:
                try:
                    resp = await client.get(sm_url)
                    if resp.status_code != 200:
                        continue
                    tree = ElementTree.fromstring(resp.content)
                    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                    urls = tree.findall(".//sm:loc", ns) or tree.findall(".//loc")
                    urls_found = [u.text for u in urls if u.text]
                    result["sitemaps"].append({
                        "url": sm_url,
                        "total_urls": len(urls_found),
                        "sample_urls": urls_found[:5],
                    })
                except Exception:
                    continue

        # 3. Conflictos: URLs en sitemaps que estan en Disallow
        disallowed = [v for k, v in result["robots_txt"].items() if k.lower() == "disallow" and v and v != "/"]
        if disallowed and result["sitemaps"]:
            result["issues"].append({
                "type": "warning",
                "msg": f"Se encontraron {len(disallowed)} reglas Disallow. Revisar que no bloqueen contenido indexable.",
            })

        if not result["sitemaps"]:
            result["issues"].append({"type": "warning", "msg": "No se encontraron sitemaps XML accesibles."})

        return result

    async def _check_ai_overview(self, keyword: str) -> dict:
        """Verifica si una keyword activa AI Overview en Google."""
        result = {"keyword": keyword, "has_ai_overview": False, "sources": [], "summary": ""}

        # Buscar en la web y extraer resultados para detectar AI Overview
        try:
            search_result = await self._wigolo.search(keyword, max_results=10)
        except Exception as exc:
            return {"error": f"Error en busqueda: {exc}"}

        # Buscar palabras clave que indiquen AI Overview en los resultados
        ai_indicators = [
            "ai overview", "ai-generated", "ai generated", "generative ai",
            "respuesta de ia", "resumen de ia", "inteligencia artificial",
            "duckduckgo ai", "ai answer",
        ]

        raw = str(search_result).lower()
        matched = [w for w in ai_indicators if w in raw]

        # Extraer URLs relevantes del resultado de busqueda
        urls = set()
        if isinstance(search_result, dict):
            for item in search_result.get("results", search_result.get("items", [])):
                if isinstance(item, dict) and item.get("url"):
                    urls.add(item["url"])
                elif isinstance(item, dict) and item.get("link"):
                    urls.add(item["link"])

        result["has_ai_overview"] = len(matched) > 0
        result["indicators_found"] = matched
        result["sources"] = list(urls)[:5]

        if matched:
            result["summary"] = (
                f"Se detectaron indicios de AI Overview para '{keyword}'. "
                f"Palabras clave encontradas: {', '.join(matched)}. "
                f"Se recomienda verificar manualmente en Google."
            )

        return result

    async def execute(
        self, tool_name: str, arguments: str, tool_call_id: str
    ) -> ToolResult:
        """Ejecuta una tool y devuelve el resultado formateado."""
        handler = self._handlers.get(tool_name)
        if handler is None:
            content = json.dumps({"error": f"Tool desconocida: {tool_name}"})
        else:
            try:
                args = json.loads(arguments) if isinstance(arguments, str) else arguments
                result = await handler(**args)
                content = json.dumps(result, ensure_ascii=False, default=str)
            except Exception as exc:
                content = json.dumps({"error": str(exc)})

        return ToolResult(tool_call_id=tool_call_id, content=content)


# ============================================================
# Agent Orchestrator
# ============================================================

SYSTEM_PROMPT = """Eres un agente SEO profesional. Tu trabajo es ayudar con investigacion y analisis SEO usando herramientas especializadas:

**Wigolo** (gratis, ilimitado): busqueda web, extraccion de paginas, crawl de sitios, investigacion de temas. Usalo para:
- Analizar SERPs manualmente (quien rankea, que contenido hay)
- Extraer estructuras on-page (H1, meta tags, schema markup)
- Investigar tendencias y temas
- Buscar oportunidades de link building

**OpenSEO** (datos estructurados via DataForSEO): volumen de keywords, dificultad, CPC, backlinks, trafico de dominios. Usalo para:
- Datos cuantitativos de keywords (volumen exacto, dificultad, CPC)
- Analisis de trafico de competidores
- Perfiles de backlinks

**PageSpeed Insights** (gratis, sin limite practico): analisis de velocidad web y Core Web Vitals. Usalo para:
- Diagnosticar rendimiento de cualquier sitio web
- Obtener LCP, CLS, INP, TTFB, FCP
- Recomendaciones de mejora de velocidad

Reglas:
1. Para datos CUANTITATIVOS de keywords (volumen, CPC, dificultad) → usa OpenSEO.
2. Para analisis CUALITATIVO (contenido, estructura, SERPs) → usa Wigolo.
3. Para diagnosticar VELOCIDAD y RENDIMIENTO web → usa PageSpeed Insights.
4. Cuando el usuario pida un analisis completo, combina todas las fuentes disponibles.
5. Se concreto, cita fuentes, da numeros cuando los tengas.
6. Responde en español a menos que el usuario pregunte en otro idioma.
7. Si una tool falla, explica que paso y ofrece alternativas."""


@dataclass
class AgentConfig:
    model: str = field(default_factory=lambda: config.llm.model)
    temperature: float = config.llm.temperature
    max_tokens: int = config.llm.max_tokens


class SEOAgent:
    """Agente SEO que orquesta DeepSeek + Wigolo + OpenSEO."""

    def __init__(
        self,
        wigolo_client: WigoloClient,
        openseo_client: OpenSEOClient,
        agent_config: AgentConfig | None = None,
    ) -> None:
        self._llm = AsyncOpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
        )
        self._executor = ToolExecutor(wigolo_client, openseo_client)
        self._cfg = agent_config or AgentConfig()
        self._messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self._tool_calls_log: list[dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        """Agrega un mensaje al historial de conversacion."""
        self._messages.append({"role": role, "content": content})

    @property
    def history(self) -> list[dict[str, Any]]:
        """Historial completo de la conversacion (sin el system prompt)."""
        return self._messages[1:]  # skip system

    @property
    def tool_calls_log(self) -> list[dict[str, Any]]:
        """Historial de tool calls ejecutadas en esta sesion."""
        return self._tool_calls_log

    def reset(self) -> None:
        """Reinicia la conversacion (mantiene el system prompt)."""
        self._messages = [self._messages[0]]
        self._tool_calls_log = []

    async def run_streaming(self, user_message: str) -> AsyncIterator[str]:
        """Ejecuta el agente con streaming de tokens."""
        self.add_message("user", user_message)

        full_response = ""
        async for chunk in self._call_llm_streaming():
            full_response += chunk
            yield chunk

        self.add_message("assistant", full_response)

    async def _call_llm_streaming(self) -> AsyncIterator[str]:
        """Llama al LLM con streaming, manejando tool calls."""
        messages = list(self._messages)

        while True:
            stream = await self._llm.chat.completions.create(
                model=self._cfg.model,
                messages=messages,
                tools=ALL_TOOLS,
                temperature=self._cfg.temperature,
                max_tokens=self._cfg.max_tokens,
                stream=True,
            )

            # Acumula tool calls del stream
            tool_calls_acc: dict[int, dict[str, Any]] = {}
            content_acc = ""

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                # Acumula tool calls
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {
                                "id": tc_delta.id or "",
                                "function": {"name": "", "arguments": ""},
                            }
                        if tc_delta.id:
                            tool_calls_acc[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_acc[idx]["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_acc[idx]["function"]["arguments"] += tc_delta.function.arguments

                # Acumula contenido
                if delta.content:
                    content_acc += delta.content
                    yield delta.content

            # Si hubo tool calls, ejecutarlos y continuar
            if tool_calls_acc:
                ordered_tcs = [tool_calls_acc[i] for i in sorted(tool_calls_acc)]

                messages.append({
                    "role": "assistant",
                    "content": content_acc or None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": tc["function"],
                        }
                        for tc in ordered_tcs
                    ],
                })

                for tc in ordered_tcs:
                    tool_result = await self._executor.execute(
                        tc["function"]["name"],
                        tc["function"]["arguments"],
                        tc["id"],
                    )
                    # Registrar tool call para el dashboard
                    self._tool_calls_log.append({
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                        "ts": len(self._tool_calls_log),
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_result.tool_call_id,
                        "content": tool_result.content,
                    })

                # Continua el loop para la respuesta final
                continue

            # Respuesta final
            return

"""
SEO Agent — Interfaz principal con Streamlit.

Agente virtual SEO profesional que combina:
  - Wigolo MCP (investigacion web gratuita e ilimitada)
  - OpenSEO MCP (datos SEO estructurados via DataForSEO)
  - DeepSeek (orquestador LLM)

Uso:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

import streamlit as st
from datetime import datetime

# Asegura que src/ esta en el path (necesario si corres desde la raiz del proyecto)
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.orchestrator import SEOAgent
from src.mcp.clients import (
    OpenSEOClient,
    WigoloClient,
    openseo_session,
    wigolo_session,
)
from src.ui.components import tool_call_status

logging.basicConfig(level=logging.INFO)
# Silencia logs ruidosos del SDK MCP durante limpieza
logging.getLogger("asyncio").setLevel(logging.WARNING)
logger = logging.getLogger("seo-agent")


# ============================================================
# Event loop persistente
# ============================================================

@st.cache_resource
def _get_loop() -> asyncio.AbstractEventLoop:
    """Crea un event loop persistente que sobrevive re-runs de Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="SEO Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS Minimal
# ============================================================

st.markdown("""
<style>
    /* Metric cards mas compactas */
    [data-testid="stMetric"] {
        padding: 0.5rem 1rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    /* Chat messages mas legibles */
    .stChatMessage {
        font-size: 0.95rem;
    }
    /* Sidebar dark theme */
    [data-testid="stSidebar"] {
        background: #0f1117;
    }
    [data-testid="stSidebar"] * {
        color: #e0e2e6;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #e0e2e6;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6 {
        color: #f0f2f6;
    }
    [data-testid="stSidebar"] hr {
        border-color: #2e3038;
    }
    [data-testid="stSidebar"] .stButton button {
        background: #1e2030;
        color: #e0e2e6;
        border: 1px solid #2e3038;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #2a2d3e;
        border-color: #0066FF;
    }
    [data-testid="stSidebar"] .stExpander {
        background: transparent;
    }
    [data-testid="stSidebar"] .stExpander summary {
        color: #a0a2a6;
    }
    [data-testid="stSidebar"] a {
        color: #4a9eff;
    }
    [data-testid="stSidebar"] a:hover {
        color: #7ab8ff;
    }
    /* Ocultar navegacion nativa de Streamlit para poner la nuestra */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    /* Page links en sidebar oscuro */
    [data-testid="stSidebar"] .stPageLink {
        background: #1e2030;
        border: 1px solid #2e3038;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] .stPageLink:hover {
        border-color: #0066FF;
    }
    [data-testid="stSidebar"] .stPageLink p {
        color: #e0e2e6 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Session State — Manejo de conexiones MCP y agente
# ============================================================

def _init_session_state() -> None:
    """Inicializa el session state de Streamlit."""
    defaults = {
        "messages": [],          # Historial del chat
        "agent_ready": False,    # Si las conexiones MCP estan vivas
        "agent": None,           # Instancia de SEOAgent
        "mcp_status": {          # Estado de cada MCP
            "wigolo": "disconnected",
            "openseo": "disconnected",
        },
        "seo_stats": {           # Dashboard KPIs
            "keywords": [],
            "domains": [],
            "serps": [],
            "pagespeed": [],
            "tool_count": 0,
        },
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _extract_seo_stats() -> None:
    """Escanea el historial de tool calls y actualiza las estadisticas del dashboard."""
    stats = st.session_state.seo_stats
    agent = st.session_state.agent
    if not agent:
        return

    keywords = set(stats["keywords"])
    domains = set(stats["domains"])
    serps = set(stats["serps"])
    pagespeed = list(stats["pagespeed"])
    tool_count = len(agent.tool_calls_log)

    for tc in agent.tool_calls_log:
        name = tc["name"]
        try:
            args = json.loads(tc["arguments"])
        except Exception:
            continue

        if name == "openseo_research_keywords":
            keywords.update(args.get("keywords", []))
        elif name == "openseo_domain_overview":
            if args.get("domain"):
                domains.add(args["domain"])
        elif name == "openseo_serp_results":
            for q in args.get("queries", []):
                if isinstance(q, dict) and q.get("keyword"):
                    serps.add(q["keyword"])
        elif name == "wigolo_search":
            q = args.get("query", "")
            if isinstance(q, str):
                keywords.add(q)
            elif isinstance(q, list):
                keywords.update(q)
        elif name == "wigolo_fetch":
            if args.get("url"):
                domains.add(args["url"])
        elif name == "pagespeed_analyze":
            ps = {"url": args.get("url", ""), "strategy": args.get("strategy", "mobile")}
            pagespeed.append(ps)

    st.session_state.seo_stats = {
        "keywords": sorted(keywords),
        "domains": sorted(domains),
        "serps": sorted(serps),
        "pagespeed": pagespeed[-5:],
        "tool_count": tool_count,
    }


_init_session_state()


# ============================================================
# Conexion a MCP Servers
# ============================================================

async def _close_mcp_sessions() -> None:
    """Cierra sesiones MCP previas si existen (evita leaks en re-runs)."""
    for ctx_key, sess_key in [("_wigolo_ctx", "_wigolo_sess"), ("_openseo_ctx", "_openseo_sess")]:
        ctx = st.session_state.pop(ctx_key, None)
        sess = st.session_state.pop(sess_key, None)
        if ctx is not None:
            try:
                await ctx.__aexit__(None, None, None)
            except Exception:
                pass  # ignora errores de limpieza — el proceso hijo ya murio


async def _connect_mcp() -> tuple[WigoloClient, OpenSEOClient] | None:
    """Conecta a ambos servidores MCP y devuelve los clientes."""
    # Cierra sesiones previas primero
    await _close_mcp_sessions()

    wigolo_ctx = wigolo_session()
    openseo_ctx = openseo_session()

    try:
        wigolo_sess = await wigolo_ctx.__aenter__()
        st.session_state.mcp_status["wigolo"] = "connected"
    except Exception as exc:
        st.session_state.mcp_status["wigolo"] = f"error: {exc}"
        return None

    try:
        openseo_sess = await openseo_ctx.__aenter__()
        st.session_state.mcp_status["openseo"] = "connected"
    except Exception as exc:
        st.session_state.mcp_status["openseo"] = f"error: {exc}"
        # Wigolo solo sigue funcionando — OpenSEO es opcional
        openseo_sess = None

    wigolo = WigoloClient(wigolo_sess)
    openseo = OpenSEOClient(openseo_sess) if openseo_sess else None

    # Guarda las sesiones para cerrarlas despues
    st.session_state._wigolo_ctx = wigolo_ctx
    st.session_state._openseo_ctx = openseo_ctx
    st.session_state._wigolo_sess = wigolo_sess
    st.session_state._openseo_sess = openseo_sess

    return wigolo, openseo


def _run_async_connect() -> None:
    """Wrapper sincrono para conectar MCP desde Streamlit con event loop persistente."""
    if st.session_state.agent_ready:
        return

    loop = _get_loop()

    with st.spinner("Conectando a servidores MCP..."):
        try:
            result = loop.run_until_complete(_connect_mcp())
        except Exception as exc:
            st.error(f"Error conectando MCP: {exc}")
            return

    if result is None:
        st.error("No se pudo conectar a Wigolo. ¿Esta instalado? Ejecuta: npx wigolo doctor")
        return

    wigolo_client, openseo_client = result

    if openseo_client is None:
        st.warning(
            "OpenSEO no esta disponible (Docker no corriendo?). "
            "El agente funcionara solo con Wigolo — sin datos estructurados de keywords/backlinks."
        )
        # Crea un dummy OpenSEO client que devuelve errores descriptivos
        class _DummyOpenSEO:
            """Captura cualquier llamada a tool de OpenSEO y devuelve error."""
            async def __getattr__(self, name):
                return lambda **kw: {"error": f"OpenSEO no disponible ({name})."}
        openseo_client = _DummyOpenSEO()

    agent = SEOAgent(wigolo_client, openseo_client)
    st.session_state.agent = agent
    st.session_state.agent_ready = True


# ============================================================
# Panel de Capacidades — datos
# ============================================================

CAPABILITY_CATEGORIES: list[dict] = [
    {
        "icon": "🚦",
        "title": "Velocidad y Rendimiento",
        "examples": [
            "Analiza la velocidad de mi web",
            "Compara mobile vs desktop de example.com",
            "¿Cómo le va a nike.com en Core Web Vitals?",
            "Dame recomendaciones para mejorar el rendimiento de mi sitio",
            "¿Qué tan rápido carga databiq.com?",
        ],
    },
    {
        "icon": "🔍",
        "title": "Auditoría SEO",
        "examples": [
            "Haz una auditoría on-page completa de nike.com",
            "Valida los sitemaps de mi sitio",
            "Analiza el schema markup de example.com",
            "¿Mi web tiene errores de indexación?",
            "Revisa los meta tags y headings de mi web",
            "Analiza la estructura de internal linking de example.com",
        ],
    },
    {
        "icon": "🔑",
        "title": "Keywords y SERP",
        "examples": [
            "Investiga 'zapatos running Colombia'",
            "¿Quién rankea para 'business intelligence'?",
            "¿'beneficios SEO' tiene AI Overview?",
            "Dame keywords de baja dificultad para mi nicho",
            "¿Qué SERP features aparecen para 'data science'?",
        ],
    },
    {
        "icon": "📊",
        "title": "Competencia y Mercado",
        "examples": [
            "¿Quiénes son competidores orgánicos de databiq.com?",
            "Analiza el tráfico estimado de nike.com",
            "Compara el perfil de backlinks de dos dominios",
            "Investiga el mercado de BI en Colombia 2026",
            "Tendencias de SEO para ecommerce este año",
        ],
    },
    {
        "icon": "🔗",
        "title": "Link Building",
        "examples": [
            "Encuentra sitios similares a databiq.com para guest posting",
            "Analiza el perfil de backlinks de mi competidor",
            "Busca oportunidades de link building para mi web",
            "¿Qué dominios de referencia tiene example.com?",
        ],
    },
    {
        "icon": "📈",
        "title": "Contenido",
        "examples": [
            "Analiza la estructura de contenido de nike.com",
            "¿Qué temas cubre mi competidor que yo no?",
            "Compara mi contenido con el de example.com",
            "¿Qué tan optimizado está el contenido de mi blog?",
        ],
    },
]


def _render_capability_panel() -> None:
    """Panel '¿Qué puedo preguntar?' con tarjetas de capacidad × ejemplo."""
    MAX_VISIBLE = 3
    with st.expander("💡 ¿Qué puedo preguntar?", expanded=False):
        for i in range(0, len(CAPABILITY_CATEGORIES), 2):
            cols = st.columns(2)
            for col_idx in range(2):
                cat_idx = i + col_idx
                if cat_idx >= len(CAPABILITY_CATEGORIES):
                    break
                cat = CAPABILITY_CATEGORIES[cat_idx]
                with cols[col_idx]:
                    st.markdown(f"**{cat['icon']} {cat['title']}**")
                    for ex_idx, ex in enumerate(cat["examples"]):
                        if ex_idx == MAX_VISIBLE:
                            with st.expander(f"Ver {len(cat['examples']) - MAX_VISIBLE} más..."):
                                for ex2 in cat["examples"][MAX_VISIBLE:]:
                                    if st.button(ex2, use_container_width=True, key=f"cap_{cat_idx}_{hash(ex2) % 10_000_000}"):
                                        st.session_state._pending_prompt = ex2
                                        st.rerun()
                            break
                        if st.button(ex, use_container_width=True, key=f"cap_{cat_idx}_{ex_idx}"):
                            st.session_state._pending_prompt = ex
                            st.rerun()


# ============================================================
# Sidebar
# ============================================================

def _render_sidebar() -> None:
    """Sidebar profesional con identidad visual, estado y controles."""
    with st.sidebar:
        # ── Header ──
        st.markdown("""
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:12px'>
            <div style='
                background:linear-gradient(135deg,#0066FF,#00D4FF);
                width:36px;height:36px;border-radius:10px;
                display:flex;align-items:center;justify-content:center;
                font-size:20px;color:white;font-weight:bold;
            '>S</div>
            <div>
                <div style='font-weight:700;font-size:1.1rem;line-height:1.2'>SEO Agent</div>
                <div style='font-size:0.7rem;color:#888;'>v0.3 &middot; DeepSeek + Wigolo</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navegacion ──
        col1, col2 = st.columns(2)
        with col1:
            st.page_link("streamlit_app.py", label="💬 Chat", use_container_width=True)
        with col2:
            st.page_link("pages/dashboard.py", label="📊 Dashboard", use_container_width=True)

        st.divider()

        # ── Estado de conexión ──
        st.markdown("##### 🔌 Conexiones")

        w_status = st.session_state.mcp_status.get("wigolo", "disconnected")
        o_status = st.session_state.mcp_status.get("openseo", "disconnected")

        def _status_tag(name: str, status: str, ok_color: str, ko_color: str) -> None:
            ok = status == "connected"
            bg = ok_color if ok else ko_color
            icon = "●" if ok else "○"
            label = "Conectado" if ok else "No disponible"
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0'>"
                f"  <span style='color:{bg};font-size:12px'>{icon}</span>"
                f"  <span style='font-size:0.85rem;font-weight:500'>{name}</span>"
                f"  <span style='margin-left:auto;font-size:0.7rem;color:{bg};"
                f"        background:{bg}20;padding:1px 8px;border-radius:8px;'>{label}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        _status_tag("Wigolo", w_status, "#00CC66", "#FF4B4B")
        _status_tag("OpenSEO", o_status, "#00CC66", "#FFA500")

        st.divider()

        # ── Acciones ──
        st.markdown("##### ⚙️ Acciones")
        if st.button("🗑️  Limpiar conversación", use_container_width=True, type="secondary"):
            if st.session_state.agent:
                st.session_state.agent.reset()
            st.session_state.messages = []
            st.rerun()

        # ── Información ──
        with st.expander("ℹ️  Acerca de"):
            st.markdown(f"""
            <div style='font-size:0.8rem;line-height:1.6'>
                <b>SEO Agent</b> — v0.3<br>
                Agente virtual SEO con lenguaje natural.<br><br>
                <b>Stack:</b>
                <ul style='margin:0;padding-left:16px'>
                    <li>🧠 DeepSeek V4 Flash</li>
                    <li>🔍 Wigolo (web intelligence)</li>
                    <li>📊 OpenSEO (datos SEO)</li>
                    <li>🎨 Streamlit</li>
                </ul>
                <br>
                <a href='https://github.com/every-app/open-seo' target='_blank'>Ver en GitHub →</a>
                <br><br>
                <span style='color:#888;font-size:0.7rem'>
                    Sesión iniciada: {datetime.now().strftime("%H:%M")}
                </span>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# Chat Interface
# ============================================================

def _render_chat() -> None:
    """Renderiza el historial del chat y maneja nueva entrada del usuario."""

    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Panel de capacidades (visible hasta el primer mensaje)
    if not st.session_state.messages:
        _render_capability_panel()

    # Input del usuario
    prompt = st.chat_input(
        "Pregunta algo sobre SEO...",
        key="chat_input",
    )

    # Procesar prompt pendiente (de los suggestion buttons)
    pending = st.session_state.pop("_pending_prompt", None)
    if pending:
        prompt = pending

    if not prompt:
        return

    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Llamar al agente con streaming (usa el event loop persistente)
    with st.chat_message("assistant"):
        try:
            loop = _get_loop()
            response = loop.run_until_complete(
                _stream_agent_response(prompt)
            )
        except Exception as exc:
            response = f"❌ Error: {exc}"
            logger.exception("Agent error")

    st.session_state.messages.append({"role": "assistant", "content": response})
    _extract_seo_stats()


async def _stream_agent_response(prompt: str) -> str:
    """Ejecuta el agente mostrando tools en tiempo real y texto en streaming."""
    agent: SEOAgent = st.session_state.agent
    seen = len(agent.tool_calls_log)

    with st.status("🔍 Analizando...", expanded=True) as status:
        tool_area = st.empty()
        placeholder = st.empty()
        full_response = ""

        async for chunk in agent.run_streaming(prompt):
            # Mostrar nuevas tool calls ejecutadas
            new_tools = agent.tool_calls_log[seen:]
            if new_tools:
                with tool_area.container():
                    for tc in new_tools:
                        tool_call_status(tc["name"], "...", "done")
                seen += len(new_tools)

            full_response += chunk
            placeholder.markdown(full_response + "▌")

        status.update(label="✅ Análisis completo", state="complete")
        placeholder.markdown(full_response)
        return full_response


# ============================================================
# Main
# ============================================================

def main() -> None:
    """Entry point principal de la app Streamlit."""

    _render_sidebar()

    st.title("🔍 SEO Agent")
    st.caption(
        "Tu agente virtual de SEO — potenciado por DeepSeek, Wigolo y OpenSEO"
    )

    # Conectar MCP al iniciar
    if not st.session_state.agent_ready:
        _run_async_connect()
        if st.session_state.agent_ready:
            st.rerun()
        return

    _render_chat()


if __name__ == "__main__":
    main()

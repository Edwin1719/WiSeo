"""
Dashboard de KPIs SEO — alimentado por datos de las consultas del agente.
"""

from __future__ import annotations

import streamlit as st
from src.ui.components import kpi_row, keyword_table, serp_results_table

st.set_page_config(
    page_title="Dashboard SEO",
    page_icon="📊",
    layout="wide",
)

# ── Leer datos desde session_state ──
stats = st.session_state.get("seo_stats", {})
keywords = stats.get("keywords", [])
domains = stats.get("domains", [])
serps = stats.get("serps", [])
pagespeed = stats.get("pagespeed", [])
tool_count = stats.get("tool_count", 0)

st.title("📊 Dashboard SEO")
st.caption("KPIs y metricas recopiladas durante la sesion del agente")

# ── KPIs principales ──
kpi_row([
    {"label": "Keywords Investigadas", "value": len(keywords), "icon": "🔑"},
    {"label": "Dominios Analizados", "value": len(domains), "icon": "🌐"},
    {"label": "SERPs Consultados", "value": len(serps), "icon": "📈"},
    {"label": "Tools Ejecutadas", "value": tool_count, "icon": "⚙️"},
    {"label": "PageSpeed Analisis", "value": len(pagespeed), "icon": "🚦"},
])

st.divider()

# ── Keywords ──
st.subheader("🔑 Keywords Investigadas")
if keywords:
    kw_data = [{"keyword": k} for k in keywords]
    keyword_table(kw_data)
else:
    st.info("Aun no se han investigado keywords. Haz preguntas al agente en el Chat.")

# ── Dominios ──
st.subheader("🌐 Dominios Analizados")
if domains:
    for d in domains:
        st.markdown(f"- {d}")
else:
    st.info("Aun no se han analizado dominios.")

# ── PageSpeed ──
st.subheader("🚦 PageSpeed Insights")
if pagespeed:
    for ps in pagespeed:
        st.markdown(f"- {ps['url']} ({ps['strategy']})")
else:
    st.info("Aun no se han ejecutado analisis de velocidad.")

# ── SERPs ──
st.subheader("📈 SERPs Consultados")
if serps:
    serp_results_table([{"keyword": s} for s in serps])
else:
    st.info("Aun no se han consultado SERPs.")

# ── Actividad reciente ──
st.divider()
st.subheader("📋 Ultimas consultas")
messages = st.session_state.get("messages", [])
user_msgs = [m for m in messages if m["role"] == "user"]
if user_msgs:
    for m in user_msgs[-5:]:
        st.markdown(f"- {m['content'][:100]}...")
else:
    st.info("Aun no hay consultas en esta sesion.")

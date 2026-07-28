"""
Componentes UI reutilizables para el SEO Agent.

Cards de metricas, tablas de keywords, visualizaciones de datos SEO.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# Metric Cards
# ============================================================

def metric_card(
    label: str,
    value: str | int | float,
    delta: str | None = None,
    *,
    icon: str = "",
    help_text: str = "",
) -> None:
    """Muestra una metrica con estilo de card."""
    delta_color = "normal"
    if delta and delta.startswith("+"):
        delta_color = "normal"
    elif delta and delta.startswith("-"):
        delta_color = "inverse"

    label_text = f"{icon} {label}" if icon else label
    st.metric(
        label=label_text,
        value=value,
        delta=delta,
        delta_color=delta_color,
        border=True,
        help=help_text or None,
    )


def kpi_row(metrics: list[dict]) -> None:
    """Fila de KPIs en cards horizontales.

    Cada dict debe tener: label, value. Opcional: delta, icon.
    """
    with st.container():
        cols = st.columns(len(metrics))
        for col, m in zip(cols, metrics):
            with col:
                metric_card(
                    label=m["label"],
                    value=m["value"],
                    delta=m.get("delta"),
                    icon=m.get("icon", ""),
                    help_text=m.get("help", ""),
                )


# ============================================================
# Keyword Research Display
# ============================================================

def keyword_table(keywords_data: list[dict]) -> None:
    """Tabla de keywords con metricas SEO.

    Espera lista de dicts con keys como:
    keyword, search_volume, difficulty, cpc, competition
    """
    if not keywords_data:
        st.info("No hay datos de keywords para mostrar.")
        return

    df = pd.DataFrame(keywords_data)

    # Renombrar columnas para display
    column_map = {
        "keyword": "Keyword",
        "search_volume": "Vol. Búsqueda",
        "difficulty": "Dificultad",
        "cpc": "CPC (USD)",
        "competition": "Competencia",
        "monthly_searches": "Vol. Mensual",
    }

    display_cols = [c for c in column_map if c in df.columns]
    df_display = df[display_cols].rename(columns=column_map)

    # Formatear numeros
    st_col_config = {}
    for col_name in df_display.columns:
        if "Vol." in col_name or "CPC" in col_name:
            st_col_config[col_name] = st.column_config.NumberColumn(format="%,d")
        elif "Dificultad" in col_name:
            st_col_config[col_name] = st.column_config.ProgressColumn(
                format="%d", min_value=0, max_value=100
            )
        elif "Competencia" in col_name:
            st_col_config[col_name] = st.column_config.NumberColumn(format="%.2f")

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config=st_col_config or None,
    )


# ============================================================
# SERP Results Display
# ============================================================

def serp_results_table(serp_data: list[dict]) -> None:
    """Tabla de resultados SERP: posicion, titulo, URL, tipo."""
    if not serp_data:
        st.info("No hay datos SERP para mostrar.")
        return

    df = pd.DataFrame(serp_data)

    # Seleccionar columnas utiles
    cols = []
    for c in ["position", "rank_position", "title", "url", "description", "type"]:
        if c in df.columns:
            cols.append(c)

    if not cols:
        st.dataframe(df, use_container_width=True, hide_index=True)
        return

    df_display = df[cols].rename(columns={
        "position": "#",
        "rank_position": "#",
        "title": "Título",
        "url": "URL",
        "description": "Descripción",
        "type": "Tipo",
    })

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn(width="small"),
            "URL": st.column_config.LinkColumn(width="medium"),
        },
    )


# ============================================================
# Domain Overview Card
# ============================================================

def domain_overview_card(domain: str, overview: dict) -> None:
    """Card resumen de un dominio con KPIs principales."""
    with st.container(border=True):
        st.subheader(f":globe_with_meridians: {domain}")

        metrics = []

        if "organic_traffic" in overview:
            metrics.append({
                "label": "Tráfico Orgánico",
                "value": f"{overview['organic_traffic']:,}",
                "icon": ":material/trending_up:",
            })
        if "traffic_cost" in overview:
            metrics.append({
                "label": "Valor Tráfico",
                "value": f"${overview['traffic_cost']:,.0f}",
                "icon": ":material/payments:",
            })
        if "total_keywords" in overview:
            metrics.append({
                "label": "Keywords",
                "value": f"{overview['total_keywords']:,}",
                "icon": ":material/search:",
            })
        if "backlinks_count" in overview or "backlinks" in overview:
            bl = overview.get("backlinks_count", overview.get("backlinks", 0))
            metrics.append({
                "label": "Backlinks",
                "value": f"{bl:,}",
                "icon": ":material/link:",
            })

        if metrics:
            kpi_row(metrics)
        else:
            st.json(overview)


# ============================================================
# Backlinks Display
# ============================================================

def backlinks_table(backlinks_data: list[dict]) -> None:
    """Tabla de backlinks con fuente, anchor, tipo."""
    if not backlinks_data:
        st.info("No hay datos de backlinks.")
        return

    df = pd.DataFrame(backlinks_data)

    rename = {
        "source": "Origen",
        "target": "Destino",
        "anchor": "Anchor Text",
        "type": "Tipo",
        "domain_authority": "DA",
        "page_authority": "PA",
        "first_seen": "Primera vez",
        "last_seen": "Última vez",
    }

    display_cols = [c for c in rename if c in df.columns]
    df_display = df[display_cols].rename(columns=rename)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Origen": st.column_config.LinkColumn(width="medium"),
            "DA": st.column_config.NumberColumn(width="small"),
        },
    )


# ============================================================
# Rank Tracking Chart
# ============================================================

def rank_tracking_chart(
    keyword_ranks: dict[str, list[dict]],
    *,
    height: int = 400,
) -> None:
    """Grafico de evolucion de rankings por keyword.

    keyword_ranks: {"keyword": [{"date": ..., "position": ...}, ...]}
    """
    if not keyword_ranks:
        st.info("No hay datos de rank tracking.")
        return

    fig = go.Figure()

    for kw, data in keyword_ranks.items():
        dates = [d.get("date", d.get("datetime", "")) for d in data]
        positions = [d.get("position", d.get("rank", 0)) for d in data]
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=positions,
                mode="lines+markers",
                name=kw,
                hovertemplate="%{x}<br>Posición: %{y}",
            )
        )

    fig.update_layout(
        title="Evolución de Rankings",
        yaxis=dict(
            title="Posición",
            autorange="reversed",  # #1 arriba
            dtick=5,
        ),
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# Tool Call Status Display
# ============================================================

def tool_call_status(tool_name: str, args: str = "", status: str = "running") -> None:
    """Muestra el estado de una tool call durante la ejecucion del agente."""
    status_icon = {
        "running": ":material/hourglass_top:",
        "done": ":material/check_circle:",
        "error": ":material/error:",
    }

    icon = status_icon.get(status, ":material/circle:")
    color = {"running": "orange", "done": "green", "error": "red"}.get(status, "gray")

    label = {
        "wigolo_search": f"Buscando: {args}",
        "wigolo_fetch": f"Cargando: {args}",
        "wigolo_extract": f"Extrayendo: {args}",
        "wigolo_crawl": f"Crawleando: {args}",
        "wigolo_research": f"Investigando: {args}",
        "openseo_research_keywords": f"Keywords: {args}",
        "openseo_domain_overview": f"Dominio: {args}",
        "openseo_serp_results": f"SERP: {args}",
        "openseo_backlinks_overview": f"Backlinks: {args}",
        "pagespeed_analyze": f"PageSpeed: {args}",
    }.get(tool_name, f"{tool_name}: {args}")

    st.markdown(f":{color}[{icon}] {label}")


# ============================================================
# PageSpeed Results Card
# ============================================================

def pagespeed_card(data: dict) -> None:
    """Muestra resultados de PageSpeed Insights con score y metricas."""
    score = data.get("score", 0)
    strategy = data.get("strategy", "mobile").capitalize()

    color = "#22C55E" if score >= 90 else "#EAB308" if score >= 50 else "#EF4444"
    label = "Bueno" if score >= 90 else "Mejorable" if score >= 50 else "Pobre"

    st.markdown(f"""
    <div style='border:1px solid #e0e0e0;border-radius:12px;padding:16px;margin:8px 0'>
        <div style='display:flex;align-items:center;gap:16px;margin-bottom:12px'>
            <div style='
                width:72px;height:72px;border-radius:50%;
                background:conic-gradient({color} {score}%, #e0e0e0 {score}%);
                display:flex;align-items:center;justify-content:center;
                font-size:1.5rem;font-weight:700;color:{color};
            '>{score}</div>
            <div>
                <div style='font-weight:600;font-size:1rem'>PageSpeed Score</div>
                <div style='color:{color};font-weight:500'>{label} ({strategy})</div>
                <div style='font-size:0.75rem;color:#888'>Lighthouse v{data.get("lighthouse_version","")}</div>
            </div>
        </div>
        <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px'>
    """, unsafe_allow_html=True)

    metrics = [
        ("LCP", data.get("lcp"), "Largest Contentful Paint"),
        ("CLS", data.get("cls"), "Cumulative Layout Shift"),
        ("INP", data.get("inp"), "Interaction to Next Paint"),
        ("TTFB", data.get("ttfb"), "Time to First Byte"),
        ("FCP", data.get("fcp"), "First Contentful Paint"),
        ("SI", data.get("si"), "Speed Index"),
    ]
    for name, value, help_text in metrics:
        val = value or "—"
        st.markdown(
            f"<div style='background:#f5f5f5;border-radius:8px;padding:8px;text-align:center'>"
            f"  <div style='font-size:0.7rem;color:#888'>{name}</div>"
            f"  <div style='font-weight:600;font-size:0.95rem'>{val}</div>"
            f"  <div style='font-size:0.6rem;color:#aaa'>{help_text}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)


# ============================================================
# Excel Export
# ============================================================

def export_to_excel(response: str, query: str = "") -> bytes:
    """Envuelve el analisis del agente en un Excel con metadata."""
    import io
    from datetime import datetime

    import pandas as pd

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame([{
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Consulta": query,
            "Analisis": response,
        }]).to_excel(writer, sheet_name="Analisis SEO", index=False)
    return buf.getvalue()

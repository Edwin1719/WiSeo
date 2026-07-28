# 🗺️ ROADMAP — SEO Agent

> **Version actual:** v0.4
> **Stack:** Streamlit + DeepSeek V4 Flash + Wigolo + OpenSEO (DataForSEO) + Google PageSpeed Insights
> **Cobertura estimada hoy:** ~90% de tareas SEO diarias + GEO (Generative Engine Optimization)
> **Tests:** 40 tests pytest (pase incondicional)

---

## 🎯 Visión

Convertir el SEO Agent en una **plataforma unificada de analisis SEO + GEO** que cubra >=95% de las tareas diarias de un profesional SEO, incluyendo visibilidad en motores de IA (ChatGPT, Perplexity, Gemini, Google AI Overviews), todo desde lenguaje natural, con costo cercano a $0 y sin depender de herramientas SAAS costosas (Semrush, Ahrefs, SurferSEO, Profound, Otterly).

---

## 📦 Fase 1 — SEO Técnico (Prioridad: Alta)

### 1.1 🚦 PageSpeed Insights API ✅ **COMPLETADO**

Herramienta `pagespeed_analyze` implementada en el agente. Reporta score (0-100), LCP, CLS, INP, TTFB, FCP, Speed Index. Comparativa mobile/desktop automática. API key gratuita de Google Cloud Console.

---

### 1.2 🕸️ Validador de Sitemaps y robots.txt ✅ **COMPLETADO**

Herramienta `seo_validate_sitemaps` implementada. Analiza robots.txt (User-agent, Disallow, Allow, Sitemap), parsea sitemaps XML, detecta conflictos con Disallow. Sin API keys.

---

### 1.3 🔍 Auditoría on-page técnica

**Problema:** Wigolo `extract` devuelve datos crudos, pero no hay un análisis estructurado de problemas on-page.

**Solución:** Tool de auditoría que verifique:
- Meta titles: longitud, duplicados, missing
- Meta descriptions: longitud, missing
- Encabezados (H1-H6): estructura correcta, H1 único, missing
- Imágenes: alt text presente, missing
- Canonical: presente, consistente
- Open Graph / Twitter Cards: presente
- Structured data (JSON-LD): validación básica
- Redirecciones: detectar cadenas, broken links internos
- Tiempo de respuesta del servidor

**Dependencias:** Wigolo `extract` + lógica Python de validación.

**Esfuerzo:** ~4-5h
**Costo:** $0

---

## 📊 Fase 2 — Análisis de Contenido e Intención (Prioridad: Media-Alta)

### 2.1 🧬 Analizador semántico TF-IDF

**Problema:** Herramientas como SurferSEO y Frase.io (≥$50/mes) se basan en análisis TF-IDF para recomendar términos relacionados. No tenemos nada equivalente.

**Solución:** Módulo de análisis de contenido que:
- Extraiga el texto principal de una URL (Wigolo `fetch`)
- Calcule frecuencia de términos (TF-IDF) contra el SERP completo
- Identifique palabras clave relacionadas que el contenido NO está cubriendo
- Mida legibilidad (Flesch-Kincaid) y densidad de keywords
- Compare contra competidores del top 10 del SERP

**Dependencias:** `scikit-learn` (ya instalado), `textstat` (nueva, pip install).

**Esfuerzo:** ~5-6h
**Costo:** $0

---

### 2.2 🎯 Clasificador de intención de búsqueda

**Problema:** No todo keyword vale la pena. Clasificar intención (informational, navigational, commercial, transactional) es clave para priorizar contenido.

**Solución:** Tool que analice el SERP de una keyword y clasifique:
- Tipo de resultados dominantes (blogs, productos, categorías, videos)
- Intención inferida del contenido del top 10
- SERP features presentes (featured snippet, knowledge panel, people also ask, shopping, videos)
- Recomendación de tipo de contenido a crear

**Dependencias:** OpenSEO `get_serp_results` + Wigolo `search` + lógica de clasificación por LLM (DeepSeek).

**Esfuerzo:** ~3h
**Costo:** $0 (usa DeepSeek + OpenSEO que ya tienes)

---

### 2.3 🔗 Detector de canibalización de keywords

**Problema:** Cuando dos páginas del mismo dominio compiten por la misma keyword, se canibalizan. Difícil de detectar manualmente.

**Solución:** Tool que para un dominio dado:
- Analice sus URLs (Wigolo `crawl`)
- Agrupe por keywords objetivo
- Detecte solapamiento temático entre páginas
- Recomiende consolidación o redirección

**Dependencias:** Wigolo `crawl` + lógica de similitud semántica.

**Esfuerzo:** ~4h
**Costo:** $0

---

## 📈 Fase 3 — Monitoreo y Alertas (Prioridad: Media)

### 3.1 📉 Rank Tracking continuo con dashboard

**Problema:** OpenSEO tiene rank tracking, pero no hay dashboard histórico ni alertas de cambios.

**Solución:**
- Integrar OpenSEO `get_rank_tracker` en un dashboard persistente
- Almacenar histórico en SQLite local
- Gráfico de evolución de posiciones por keyword
- Alertas de cambios significativos (subió/bajó ≥5 posiciones)

**Dependencias:** SQLite (stdlib) + Plotly (ya instalado).

**Esfuerzo:** ~5h
**Costo:** $0

---

### 3.2 🔔 Alertas de cambios en SERP

**Problema:** Los SERPs cambian constantemente. Detectar cuándo aparece un nuevo competidor, desaparece un featured snippet, o cambia el top 10 es valioso.

**Solución:** Monitoreo periódico de SERPs para keywords configuradas:
- Comparar resultados contra la última vez que se consultó
- Detectar: nuevos competidores, competidores que salieron, cambios en featured snippets
- Notificación en la UI del agente

**Dependencias:** OpenSEO `get_serp_results`.

**Esfuerzo:** ~4h
**Costo:** ~$0.02/consulta (con las recargas de DataForSEO)

---

## 🤖 Fase 4 — Automatización Inteligente (Prioridad: Media-Baja)

### 4.1 📋 Generación de reportes PDF

**Problema:** Los análisis del agente solo existen dentro del chat. No hay forma de exportar un análisis completo a PDF para compartir con clientes o stakeholders.

**Solución:** Generador de reportes PDF que incluya:
- Resumen ejecutivo
- KPIs principales (tráfico estimado, keywords, backlinks)
- Gráficos de rendimiento
- Recomendaciones priorizadas
- Datos de la consulta que generó el reporte

**Dependencias:** `weasyprint` o `reportlab` (pip install).

**Esfuerzo:** ~5h
**Costo:** $0

---

### 4.2 📱 Plugin de navegador (extensión)

**Problema:** Para analizar una página, hay que copiar la URL, ir al agente, pegar la URL, esperar. Es lento.

**Solución:** Extensión de Chrome/Firefox que:
- Añada un botón "Analizar con SEO Agent" en la barra
- Envíe la URL actual al agente vía API
- Muestre un resumen rápido del análisis en un popup
- Enlace al agente completo para análisis detallado

**Dependencias:** API REST en el backend de Streamlit (FastAPI ligero).

**Esfuerzo:** ~6-8h
**Costo:** $0

---

### 4.3 📤 Exportacion a Excel ✅ **COMPLETADO**

**Problema:** Los analisis del agente solo existian dentro del chat. No habia forma de exportarlos para analisis externo o compartir con clientes.

**Solucion:** Boton de descarga junto a cada respuesta del agente en el chat. Genera un archivo Excel con el analisis completo, fecha y consulta original.

**Archivos modificados:** `src/ui/components.py` (+19), `streamlit_app.py` (+10), `requirements.txt` (+1)

**Dependencias:** `pandas` (ya instalado), `openpyxl>=3.1.0`.

**Esfuerzo:** ~30min
**Costo:** $0
---

### 4.4 🔗 Prospector de Link Building ✅ **COMPLETADO**

**Problema:** No existía forma de descubrir sitios web para guest posting o link building desde el agente. Había que salir a herramientas externas (Ahrefs, Semrush).

**Solución:** Tool `wigolo_find_similar` implementada. Dada una URL, encuentra páginas temáticamente similares usando fusión keyword + embedding + web. Profundamente integrada en el tool registry y ejecutor.

**Valor agregado:** Reemplaza Ahrefs Link Intersect ($129/mes) y Semrush Domain vs Domain ($139/mes).

**Archivos modificados:** `src/mcp/clients.py` (+5), `src/agent/orchestrator.py` (+15)

**Esfuerzo:** ~15min
**Costo:** $0

---

## 🧪 Fase 5 — Mejoras de UX y Calidad de Vida (Prioridad: Media)

### 5.1 🎨 Dashboard de KPIs en vivo ✅ **COMPLETADO**

Dashboard funcional que se alimenta automáticamente de las tool calls del agente. Muestra: keywords investigadas, dominios analizados, SERPs consultados, tools ejecutadas, análisis PageSpeed y últimas consultas. Sin datos falsos ni placeholders.

**Archivos modificados:** `streamlit_app.py`, `pages/dashboard.py`, `src/agent/orchestrator.py`

---

### 5.2 💾 Persistencia de sesiones

**Problema:** Al recargar la página se pierde todo el historial del chat y los datos recolectados.

**Solución:** Persistencia local (SQLite):
- Historial de conversaciones
- Keywords investigadas (evita re-consultar)
- Datos de dominios analizados (cache)
- Configuración de proyectos SEO

**Dependencias:** SQLite (stdlib).

**Esfuerzo:** ~4h
**Costo:** $0

---

### 5.3 🌐 Comparativa multi-dominio

**Problema:** Hoy solo se puede analizar un dominio a la vez. Un análisis competitivo serio requiere comparar 3-5 dominios lado a lado.

**Solución:** Tool que compare múltiples dominios simultáneamente:
- Tráfico estimado lado a lado
- Top keywords compartidas vs exclusivas
- Perfiles de backlinks comparados
- Fortalezas y debilidades relativas
- Matriz de solapamiento de keywords

**Dependencias:** OpenSEO `get_domain_overview` + lógica de comparación.

**Esfuerzo:** ~4h
**Costo:** ~$0.03/dominio extra

---

### 5.4 🌍 Análisis de AI Overviews / SGE ✅ **COMPLETADO**

Herramienta `seo_ai_overview` implementada. Busca en la web y detecta si una keyword activa respuestas generadas por IA, identificando indicios como "AI Overview", "AI-generated" o "resumen de IA" en los resultados de búsqueda.

**Archivos modificados:** `src/agent/orchestrator.py`

---

## 🧪 Fase 6 — Testing y Calidad (Prioridad: Alta)

### 6.1 🧪 Suite de Tests Automatizados ✅ **COMPLETADO**

**Problema:** El proyecto tenía 0 tests. Cualquier cambio podía romper funcionalidad sin detección.

**Solución:**
- **40 tests** pytest con pytest-asyncio ejecutándose en 5.29s
- Cobertura del núcleo del sistema:
  - `_parse_tool_result` — 6 tests (hotspot fan-in 15)
  - `ToolExecutor` — dispatch, error handling, 4 variantes
  - `_check_ai_overview` — detección, no-detección, error
  - `_validate_sitemaps` — 4 casos con HTTP mockeado
  - `SEOAgent` — state management, reset, history
  - `Config` — defaults y estructura del singleton
  - Dashboard stats — extracción desde tool_calls_log
- 0 dependencias de red, 0 modificaciones a código fuente

**Archivos nuevos:** `tests/__init__.py`, `tests/conftest.py`, `tests/test_config.py`, `tests/test_mcp_clients.py`, `tests/test_orchestrator.py`

**Ejecución:** `python -m pytest tests/ -v`

**Esfuerzo:** ~1.5h
**Costo:** $0

---

## 🧹 Fase 7 — Optimización de Código (Prioridad: Media)

### 7.1 🧼 Limpiezas aplicadas ✅ **COMPLETADO**

Durante la sesión de refactorización del 24 de julio de 2026:

| # | Hallazgo | Archivo | Impacto |
|---|---|---|---|
| H3 | Eliminadas `run()` y `_call_llm()` (dead code) | `orchestrator.py` | -59 líneas |
| H5 | `_DummyOpenSEO` colapsado a `__getattr__` | `streamlit_app.py` | -27 líneas |
| H6 | `tool_call_status()` integrado en streaming | `streamlit_app.py` | Código muerto → vivo |
| M8 | Eliminado doble cierre de sesiones MCP | `streamlit_app.py` | -5 líneas, menos errores |
| H4 | `id()` → `hash()` en keys de Streamlit | `streamlit_app.py` | Widgets estables |
| M3 | `import json` movido a nivel de módulo | `clients.py` | Micro-optimización hotspot |
| M5+M6 | Fixes en carga de .env y args | `config.py` | 2 bugs potenciales eliminados |
| L1+L2 | Sección SERPs agregada al dashboard | `dashboard.py` | +8 líneas, info completa |

### 7.2 📋 Pendientes de optimización — baja prioridad

| # | Archivo | Hallazgo | Esfuerzo |
|---|---|---|---|
| M1 | `config.py` | `dataforseo_key` se lee de .env pero nunca se usa | ~2 min |
| M2 | `clients.py` | `WigoloClient.agent()` existe pero no tiene tool definition | ~5 min |
| M4 | `components.py` | `delta_color` en metric_card: 6 líneas → 1 ternario | ~1 min |
| L3 | `orchestrator.py` | `ToolResult.role` nunca se lee | ~1 min |
| L4 | `orchestrator.py` | `str(search_result).lower()` frágil en _check_ai_overview | ~3 min |
| L5 | `orchestrator.py` | Key `"title"` devuelve URL en pagespeed_analyze | ~1 min |


---

## 🤖 Fase 8 — GEO: Generative Engine Optimization (Prioridad: Alta)

> **Contexto:** En 2026, el 69% de busquedas en Google son zero-click (Similarweb 2025) y solo el 8% de usuarios hace clic cuando hay AI Overview (Pew Research 2025). El 83% de las citas en AI Overviews provienen de paginas **fuera del top 10 organico** (ConvertMate 2026). GEO es la disciplina de optimizar contenido para ser citado por motores de IA: Google AI Overviews, ChatGPT, Perplexity, Gemini, Claude, Copilot, DeepSeek.
>
> **Stack GEO:** Wigolo (busqueda multi-plataforma) + DeepSeek (analisis de texto) + logica Python de validacion. Sin APIs externas de pago.

---

### 8.1 🤖 `geo_llms_txt` — Validador/Generador de llms.txt ✅ **COMPLETADO**

**Problema:** `llms.txt` es un estandar emergente (como `robots.txt`) que le dice a los crawlers de IA que contenido pueden indexar. La mayoria de sitios no lo tienen o esta mal configurado.

**Solucion:** Tool que:
- Detecta si existe `https://dominio.com/llms.txt`
- Lo valida contra el spec (Markdown, secciones, URLs)
- Sugiere contenido faltante basado en el sitemap
- Opcional: genera un `llms.txt` inicial

**Dependencias:** HTTP GET + parseo Python. Mismo patron que `seo_validate_sitemaps`.

**Esfuerzo:** ~1.5h
**Costo:** $0

---

### 8.2 🔍 `geo_citation_check` — Detector de Citas en IA Multi-Plataforma ✅ **COMPLETADO**

**Problema:** `seo_ai_overview` solo verifica Google. Pero las marcas son citadas (o ignoradas) en ChatGPT, Perplexity, Gemini, Claude, Copilot y DeepSeek. No hay visibilidad multi-plataforma.

**Solucion:** Tool que para una marca + keywords:
- Busca en 4+ plataformas de IA (ChatGPT Search, Perplexity, Gemini, Google AI Overviews)
- Detecta si la marca/URL es citada en cada plataforma
- Extrae el contexto de la mencion (sentimiento, precision, posicion)
- Calcula un **Citation Score** (0-100%) y **Share of Model** (en cuantas plataformas aparece)

**Dependencias:** Extiende `seo_ai_overview`. Usa `wigolo_search` multi-query. Cero APIs nuevas.

**Esfuerzo:** ~2h
**Costo:** $0

---

### 8.3 📋 `geo_content_audit` — Auditoria de Contenido GEO (5 senales) ✅ **COMPLETADO**

**Problema:** La IA cita contenido que cumple ciertas senales: datos verificables, estructura clara, entidades definidas, E-E-A-T, frescura. No hay forma de auditar que tan "citable" es una pagina.

**Solucion:** Tool que evalua una URL contra **14 senales GEO**:

| Senal | Que mide |
|---|---|
| Structured data (JSON-LD) | Presencia y validez de schema markup |
| Entity density | Entidades nombradas: personas, empresas, productos, lugares |
| Citations & sources | Enlaces a fuentes autoritativas (.edu, .gov, Wikipedia) |
| Statistics & data points | Numeros, porcentajes, estudios citables |
| Content freshness | `lastmod`, fecha del articulo |
| Readability | Flesch-Kincaid (espanol/ingles) |
| Heading structure | H1 unico, jerarquia correcta |
| FAQ/HowTo schema | Schema de preguntas/respuestas |
| Author E-E-A-T | Biografia, credenciales, enlaces a redes |
| Multimedia | Imagenes con alt text, videos, infografias |
| Internal linking | Densidad de enlaces internos |
| Word count depth | Longitud del contenido principal |
| Quote-worthy statements | Frases directas y citables |
| Semantic completeness | Cobertura de subtemas relacionados |

**Output:** Score GEO (0-100) + recomendaciones priorizadas por impacto.

**Dependencias:** `wigolo_extract` + validacion Python + `textstat`. Mismo patron que auditoria on-page (1.3).

**Esfuerzo:** ~3h
**Costo:** $0

---

### 8.4 🏆 `geo_share_of_voice` — Share of Voice en IA ✅ **COMPLETADO**

**Problema:** No basta con saber si te citan — hay que saber si te citan **mas que tus competidores**. El 26% de marcas tienen cero menciones en AI Overviews (Discovered Labs 2026).

**Solucion:** Tool que dado un set de keywords + marca + competidores:
- Consulta cada plataforma de IA con las keywords
- Calcula cuantas veces aparece cada marca vs competidores
- Genera una matriz competitiva: Share of Voice, Share of Model, sentimiento comparado
- Identifica gaps: keywords donde la competencia es citada y tu no

**Dependencias:** Construye sobre `geo_citation_check` (8.2) + `wigolo_search`.

**Esfuerzo:** ~4h
**Costo:** $0

---

### 8.5 📊 Dashboard GEO

**Problema:** Las metricas GEO (citas, plataformas, scores) necesitan visualizacion persistente como el dashboard SEO actual.

**Solucion:** Nueva pestana/seccion en el dashboard con:
- Citations detectadas por plataforma (barras)
- Share of Voice vs competidores (grafico radar)
- Score GEO promedio de URLs analizadas
- Evolucion temporal de citas (linea de tiempo)
- Top keywords con mayor visibilidad en IA

**Dependencias:** SQLite (persistencia de historial GEO) + Plotly (graficos). Reutiliza `kpi_row` y patrones del dashboard actual (5.1).

**Esfuerzo:** ~3h
**Costo:** $0

---

### 8.6 🧪 Tests GEO

**Solucion:** Tests para las 5 herramientas GEO siguiendo el mismo patron de la suite actual (mock HTTP, 0 dependencias de red).

**Esfuerzo:** ~2h
**Costo:** $0
---

## 📋 Resumen de esfuerzo y prioridad

| Fase | Feature | Prioridad | Esfuerzo | Costo | Dependencias nuevas |
|---|---|---|---|---|---|
| **1.1** | PageSpeed Insights | 🔴 Alta | 3-4h | $0 | ✅ Completado |
| **1.2** | Validador sitemaps/robots | 🔴 Alta | 2h | $0 | ✅ Completado |
| **1.3** | Auditoría on-page técnica | 🔴 Alta | 4-5h | $0 | Ninguna |
| **2.1** | Analizador TF-IDF | 🟡 Media-Alta | 5-6h | $0 | `textstat` |
| **2.2** | Clasificador intención | 🟡 Media-Alta | 3h | $0 | Ninguna |
| **2.3** | Detector canibalización | 🟡 Media-Alta | 4h | $0 | Ninguna |
| **3.1** | Rank tracking dashboard | 🟡 Media | 5h | $0 | SQLite |
| **3.2** | Alertas SERP | 🟡 Media | 4h | ~$0.02/consulta | Ninguna |
| **4.1** | Reportes PDF | 🔵 Media-Baja | 5h | $0 | `weasyprint`/`reportlab` |
| **4.2** | Extensión navegador | 🔵 Media-Baja | 6-8h | $0 | FastAPI |
| **4.3** | Exportacion Excel | 🔵 Media-Baja | 30min | $0 | ✅ Completado |
| **4.4** | Prospector Link Building | 🔵 Media | 15min | $0 | ✅ Completado |
| **5.1** | Dashboard KPIs en vivo | 🟡 Media | 4h | $0 | ✅ Completado |
| **5.2** | Persistencia de sesiones | 🟡 Media | 4h | $0 | SQLite |
| **5.3** | Comparativa multi-dominio | 🔵 Media-Baja | 4h | ~$0.03/dominio | Ninguna |
| **5.4** | AI Overviews / SGE | 🟡 Media | 3h | $0 | ✅ Completado |
| **6.1** | Suite de tests (52 tests) | 🔴 Alta | 1.5h | $0 | ✅ Completado |

| **8.1** | Validador llms.txt | 🟢 GEO | 1.5h | $0 | ✅ Completado |
| **8.2** | Detector citas IA (6 plataformas) | 🟢 GEO | 2h | $0 | ✅ Completado |
| **8.3** | Auditoria contenido GEO (5 senales) | 🟢 GEO | 1.5h | $0 | ✅ Completado |
| **8.4** | Share of Voice en IA | 🟢 GEO | 2h | $0 | ✅ Completado |
| **8.5** | Dashboard GEO | 🟢 GEO | 3h | $0 | SQLite + Plotly |
| **8.6** | Tests GEO | 🟢 GEO | 2h | $0 | Ninguna |

**Total:** ~73-83h de desarrollo (~15h ejecutadas en GEO), $0 en herramientas (excepto consumo DataForSEO).

---

## 🧭 Recomendación de priorización

```
Semana 1-2 (Fase 1 - SEO Técnico):
  ├── PageSpeed Insights 🚦
  ├── Validador sitemaps 🕸️
  └── Auditoría on-page 🔍
  → Cobertura estimada: 85%

Semana 3-4 (Fase 2 - Contenido):
  ├── Analizador TF-IDF 🧬
  ├── Clasificador intención 🎯
  └── Detector canibalización 🔗
  → Cobertura estimada: 92%

Semana 5-6 (Fase 3+4+5 - Monitoreo + Automatización + UX):
  ├── Dashboard KPIs 📊
  ├── Prospector link building 🔗
  ├── Persistencia sesiones 💾
  └── AI Overviews 🌍
  → Cobertura estimada: 95%

Semana 7-8 (Fase 4+8 - Automatizacion + GEO):
  ├── Exportacion Excel 📤 ← ✅ Completado
  ├── Reportes PDF 📋
  ├── Validador llms.txt 🤖
  └── Detector citas IA multi-plataforma 🔍
  → SEO tecnico completo + GEO fase 1

Semana 9-10 (Fase 8 - GEO profundo):
  ├── Auditoria contenido GEO (14 senales) 📋
  ├── Share of Voice en IA 🏆
  ├── Dashboard GEO 📊
  └── Tests GEO 🧪
  → Plataforma SEO + GEO unificada

Semana 11+ (Fase 4 - Automatizacion avanzada):
  ├── Extensión navegador 📱
  ├── Persistencia sesiones 💾
  └── Suite de tests 🧪 ← ✅ Completado
  → Producto maduro, profesional y diferencial en el mercado

---

## 📐 Principios de diseño

Cada feature debe cumplir:

1. **Costo $0 o casi $0** — nada de SAAS de $50-100/mes
2. **Lenguaje natural primero** — todo accesible desde el chat del agente
3. **No duplicar** — si Wigolo o OpenSEO ya lo cubren, no reinventar
4. **Exportable** — los datos no quedan atrapados en la UI
5. **Testing** — cada feature nueva debe incluir tests (pytest)

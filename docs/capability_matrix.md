# Matriz de Capacidades — SEO Agent v0.3

## Tools disponibles (13)

| Tool | Fuente | Qué datos produce |
|---|---|---|
| `wigolo_search` | Wigolo | Resultados de búsqueda web multi-motor |
| `wigolo_fetch` | Wigolo | Contenido completo de una URL en markdown |
| `wigolo_extract` | Wigolo | Headings, meta tags, JSON-LD, schema, tablas, metadata |
| `wigolo_crawl` | Wigolo | Mapa de URLs de un sitio (BFS/DFS/sitemap) |
| `wigolo_research` | Wigolo | Reporte sintetizado multi-fuente sobre un tema |
| `wigolo_find_similar` | Wigolo | Páginas web temáticamente similares |
| `openseo_research_keywords` | OpenSEO | Volumen, dificultad, CPC, competencia por keyword |
| `openseo_domain_overview` | OpenSEO | Tráfico estimado, top keywords, posición promedio |
| `openseo_serp_results` | OpenSEO | Top 10 SERP con titles, URLs, features |
| `openseo_backlinks_overview` | OpenSEO | Total backlinks, ref domains, anchor texts, tipos |
| `pagespeed_analyze` | Google API | Score, LCP, CLS, INP, TTFB, FCP, Speed Index |
| `seo_validate_sitemaps` | Local (httpx) | robots.txt, sitemaps XML, conflictos |
| `seo_ai_overview` | Local (Wigolo) | Detección de AI Overviews en SERP |

---

## 10 capacidades para el usuario final

### 1. 🚦 Diagnóstico de Velocidad Web
**Tools involucradas:** `pagespeed_analyze`
**Lo que entrega:** Score 0-100, LCP, CLS, INP, TTFB, FCP, Speed Index, recomendaciones de mejora
**Ejemplos:**
- *"Analiza la velocidad de mi web"*
- *"¿Cómo le va a nike.com en mobile vs desktop?"*
- *"Qué tan rápido carga databiq.com"*
- *"Dame recomendaciones para mejorar el rendimiento de example.com"*
- *"Compara la velocidad de mis 3 competidores principales"*

### 2. 🔍 Auditoría Técnica On-Page
**Tools involucradas:** `wigolo_extract` + `wigolo_fetch` + razonamiento LLM
**Lo que entrega:** Análisis de titles, meta descriptions, headings (H1-H6), alt text, canonical, Open Graph, Twitter Cards, JSON-LD, schema markup, redirecciones
**Ejemplos:**
- *"Haz una auditoría on-page completa de mi sitio"*
- *"Analiza la estructura SEO de nike.com"*
- *"¿Qué errores on-page tiene databiq.com?"*
- *"Revisa los meta tags y headings de example.com/blog"*
- *"¿Está bien optimizada la página de inicio de mi competidor?"*

### 3. 🕸️ Validación de Indexación
**Tools involucradas:** `seo_validate_sitemaps` + `wigolo_crawl`
**Lo que entrega:** Estado de robots.txt, sitemaps XML, conflictos Disallow, URLs bloqueadas vs indexadas, estructura del sitio
**Ejemplos:**
- *"Valida los sitemaps de mi web"*
- *"¿Hay conflictos entre robots.txt y mi sitemap?"*
- *"Analiza la estructura de internal linking de example.com"*
- *"Mapea todas las URLs de nike.com"*
- *"¿Google puede indexar bien mi sitio?"*

### 4. 🔑 Investigación de Keywords
**Tools involucradas:** `openseo_research_keywords` + `openseo_serp_results` + `wigolo_search`
**Lo que entrega:** Volumen de búsqueda, dificultad, CPC, competencia, SERP features, quién rankea
**Ejemplos:**
- *"Investiga las keywords 'zapatos running Colombia'"*
- *"¿Qué keywords usa mi competidor para atraer tráfico?"*
- *"Dame keywords de larga cola para mi negocio"*
- *"¿Quién rankea para 'business intelligence' en USA?"*
- *"Qué keywords tienen baja dificultad pero alto volumen"*

### 5. 📊 Análisis de Competidores
**Tools involucradas:** `openseo_domain_overview` + `openseo_backlinks_overview` + `wigolo_find_similar` + `wigolo_crawl`
**Lo que entrega:** Tráfico estimado, top keywords, backlinks, dominios similares
**Ejemplos:**
- *"Analiza el tráfico de nike.com"*
- *"¿Quiénes son los competidores orgánicos de databiq.com?"*
- *"Compara mi dominio con el de mi competidor"*
- *"¿Qué dominios de referencia tiene mis competidores?"*
- *"Dame el perfil completo de backlinks de example.com"*

### 6. 🔗 Prospección de Link Building
**Tools involucradas:** `wigolo_find_similar` + `wigolo_fetch` + `wigolo_search` + `openseo_backlinks_overview`
**Lo que entrega:** Sitios similares que aceptan guest posts, oportunidades de backlinks, perfiles de enlaces
**Ejemplos:**
- *"Encuentra sitios similares a databiq.com para guest posting"*
- *"Busca oportunidades de link building para mi web"*
- *"¿Dónde puedo conseguir backlinks de calidad?"*
- *"Qué sitios en mi nicho aceptan artículos de invitados"*
- *"Analiza el perfil de backlinks de mi competidor"*

### 7. 🧬 Análisis de Contenido
**Tools involucradas:** `wigolo_extract` + `wigolo_fetch` + `wigolo_search`
**Lo que entrega:** Estructura de contenido, temas cubiertos, gap analysis, comparativa contra SERP
**Ejemplos:**
- *"Analiza el contenido de la página principal de nike.com"*
- *"¿Qué temas cubre mi competidor que yo no?"*
- *"Dame un análisis de la estructura de contenido de example.com"*
- *"Compara el contenido de mi blog con el de la competencia"*
- *"¿Qué tan bien optimizado está mi contenido?"*

### 8. 📈 Investigación de Mercado y Tendencias
**Tools involucradas:** `wigolo_research` + `wigolo_search` + `openseo_research_keywords`
**Lo que entrega:** Reporte multi-fuente con citas, tendencias, oportunidades de mercado
**Ejemplos:**
- *"Investigación de mercado BI en Colombia 2026"*
- *"Tendencias de SEO para ecommerce este año"*
- *"¿Cómo está evolucionando el mercado de IA en Latinoamérica?"*
- *"Análisis de oportunidades de negocio en数据分析"*
- *"¿Qué está pasando en la industria del SEO en 2026?"*

### 9. 🤖 Detección de AI Overviews
**Tools involucradas:** `seo_ai_overview`
**Lo que entrega:** Si una keyword activa AI Overview, fuentes citadas, indicadores
**Ejemplos:**
- *"Verifica si 'beneficios del SEO' tiene AI Overview"*
- *"¿Qué keywords de mi nicho activan respuestas de IA?"*
- *"Mi keyword principal tiene AI Overview en Google?"*
- *"¿Qué fuentes cita Google AI para 'business intelligence'?"*

### 10. 🎯 Monitoreo SERP y Tracking
**Tools involucradas:** `openseo_serp_results` + `seo_ai_overview` + `wigolo_search`
**Lo que entrega:** Posiciones, cambios en SERP, detección de nuevos competidores
**Ejemplos:**
- *"¿Quién está en el top 10 para 'data science Colombia'?"*
- *"El SERP de mi keyword cambió? Apareció un nuevo competidor?"*
- *"¿Qué featured snippets aparecen para mis keywords?"*
- *"Dame el ranking actual para mis keywords principales"*

---

## 10 → 6 categorías para la UI

Al revisar las 10 capacidades, varias se solapan conceptualmente para el usuario. Propongo agruparlas en **6 categorías** que cubren el 100% de casos de uso:

| # | Categoría | Capacidades incluidas | Tools que usa internamente |
|---|---|---|---|
| 1 | 🚦 **Velocidad y Rendimiento** | Diagnóstico velocidad web | `pagespeed_analyze` |
| 2 | 🔍 **Auditoría SEO** | On-page, indexación, sitemaps | `extract` + `fetch` + LLM, `crawl`, `validate_sitemaps` |
| 3 | 🔑 **Keywords y SERP** | Investigación keywords, SERP, AI Overviews | `research_keywords`, `serp_results`, `search`, `ai_overview` |
| 4 | 📊 **Competencia y Mercado** | Competidores, mercado, tendencias | `find_similar`, `domain_overview`, `backlinks_overview`, `research` |
| 5 | 🔗 **Link Building** | Prospección, backlinks, guest posting | `find_similar`, `fetch`, `backlinks_overview` |
| 6 | 📈 **Contenido** | Análisis de contenido, gap analysis | `extract`, `fetch`, `search` |

```
Cobertura estimada:
  ■ ■ ■ ■ ■ ■ ■ ■ ■ ■  Velocidad        (100%)
  ■ ■ ■ ■ ■ ■ ■ ■ ■ □  Auditoría       (90%)
  ■ ■ ■ ■ ■ ■ ■ ■ □ □  Keywords/SERP   (80%)
  ■ ■ ■ ■ ■ ■ ■ ■ □ □  Competencia     (80%)
  ■ ■ ■ ■ ■ ■ ■ ■ ■ □  Link Building   (90%)
  ■ ■ ■ ■ ■ ■ ■ □ □ □  Contenido       (70%)
  → Total: ~88% de tareas SEO diarias (vs 85% en v0.2)
```

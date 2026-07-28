# 🔍 Wiseo

**by Edwin Quintero Alzate — DATABiQ**

**Agente virtual de SEO + GEO inteligente** — consulta en lenguaje natural y obtén análisis profesionales de cualquier sitio web: estructura on-page, velocidad, Core Web Vitals, sitemaps, visibilidad en motores de IA, competidores y más. Sin depender de Semrush, Ahrefs ni suscripciones costosas.

---

## 🧠 El problema que resuelve

El SEO profesional tradicional requiere:
- **Múltiples herramientas** (Semrush, Ahrefs, PageSpeed, Sitebulb...) cada una con su propia suscripción
- **Curva de aprendizaje** alta para interpretar datos de fuentes distintas
- **Trabajo manual** para cruzar información de velocidad, contenido, backlinks y sitemaps
- **Costos elevados** que empiezan en $100+/mes

**SEO Agent unifica todo en una sola conversacion**, con costos de ~$0.27 por cada 1M de tokens de DeepSeek (centavos por analisis completo). **Ahora con GEO** — analiza si tu marca es citada por ChatGPT, Perplexity, Gemini, Google AI Overviews, Copilot y DeepSeek.

---

## ⚙️ Cómo lo resuelve

```
  Tu pregunta  →  DeepSeek V4  →  ¿Herramienta necesaria?  →  Wigolo / PageSpeed / OpenSEO
       ↑                         │                                   │
       └─────────────────────────┴────── respuesta final ◀───────────┘
```

DeepSeek V4 (Flash o Pro) orquesta la conversación, decide qué herramientas necesita y sintetiza los resultados en respuestas claras y accionables.

| Componente | Qué hace | Costo |
|---|---|---|
| **🧠 DeepSeek V4 Flash/Pro** | Orquestador — razona, decide, sintetiza | ~$0.27/M tokens |
| **🔍 Wigolo MCP** | Búsqueda web, extracción de contenido, crawl de sitios, research | **$0** (ilimitado) |
| **🚦 Google PageSpeed Insights** | Velocidad, Core Web Vitals, diagnóstico de rendimiento | **$0** (25k/día) |
| **📊 OpenSEO + DataForSEO** *(opcional)* | Keywords, backlinks, SERPs, rank tracking | ~$0.02-0.05/consulta |

---

## ✨ Capacidades actuales

### 🚦 PageSpeed Insights
- Score de rendimiento (0-100) en mobile y desktop
- Métricas: LCP, CLS, INP, TTFB, FCP, Speed Index
- Recomendaciones automáticas de mejora

### 🕸️ Validador de Sitemaps y robots.txt
- Parseo de directivas robots.txt (User-agent, Disallow, Allow, Sitemap)
- Validación de sitemaps XML (índice y hojas)
- Detección de conflictos entre Disallow y URLs incluidas en sitemap

### 🔍 Investigación web (Wigolo)
- Búsqueda multi-motor con reranking semántico
- Extracción de contenido, headings, schema markup, metadatos
- Crawl multi-página (BFS, DFS, sitemap)
- Investigación profunda de temas y tendencias
- 🔗 **Prospector de similares**: descubre páginas web temáticamente similares para link building, análisis competitivo y guest posting ($0)

### 🤖 Detección de AI Overviews
- Verifica si una keyword activa respuestas generadas por IA en buscadores
- Identifica fuentes citadas en los AI Overviews
- Recomienda optimización para aparecer en resultados de IA


### 🤖 GEO — Generative Engine Optimization *(nuevo)*
- **Validador llms.txt**: detecta y valida llms.txt para crawlers de IA (ChatGPT, Perplexity, Gemini)
- **Detector de citas en IA**: verifica si tu marca es citada en 6 plataformas (Google AI Overviews, ChatGPT Search, Perplexity, Gemini, Copilot, DeepSeek)
- **Auditoria de contenido GEO**: score 0-100 con 5 senales (structured data, estadisticas, headings, frescura, profundidad)
- **Share of Voice**: ranking competitivo de visibilidad en IA vs competidores
- **Sin APIs de pago**: todo funciona con Wigolo + DeepSeek, $0 adicional

### 📊 Dashboard de KPIs
- Keywords investigadas, dominios analizados, SERPs consultados
- Tools ejecutadas y análisis PageSpeed realizados
- Se actualiza automáticamente con cada consulta

### 📈 OpenSEO *(requiere DataForSEO)*
- Volumen de búsqueda exacto, dificultad y CPC
- Perfil de backlinks y dominios de referencia
- Resultados SERP en vivo
- Rank tracking histórico

### 🧪 Suite de Tests
- **52 tests** — pytest + pytest-asyncio
- Cobertura del nucleo: config, parsing MCP, dispatch de tools, deteccion AI Overview, validacion sitemaps, estado del agente, GEO (llms.txt, citation check, content audit, share of voice)
- Mocks de servidores MCP y HTTP externos — 0 dependencias de red en los tests
- Ejecucion: `python -m pytest tests/ -v`

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| **Frontend** | Streamlit 1.60+ |
| **Orquestador** | DeepSeek V4 Flash/Pro (API compatible OpenAI) |
| **Web Intelligence** | Wigolo v0.2+ (MCP via `npx`) |
| **SEO Data** | OpenSEO v0.0.11 (Docker self-hosted) + DataForSEO API |
| **Velocidad** | Google PageSpeed Insights API |
| **Lenguaje** | Python ≥3.11 |

---

## 📦 Instalación

### Requisitos

- Python ≥ 3.11
- Node.js ≥ 20
- [Wigolo](https://www.npmjs.com/package/wigolo) — `npx wigolo init`
- Docker Desktop *(solo para OpenSEO)*
- API key de [DeepSeek](https://platform.deepseek.com/api_keys)
- API key de Google Cloud [PageSpeed Insights](https://console.cloud.google.com/apis/library)

### Pasos rápidos

```bash
# 1. Clonar e instalar dependencias
pip install -r requirements.txt

# 2. Configurar .env (ver .env.example)
cp .env.example .env
# Completa: DEEPSEEK_API_KEY, GOOGLE_PAGESPEED_API_KEY

# 3. Iniciar Wigolo (si no lo has hecho)
npx wigolo init

# 4. Arrancar la app
streamlit run streamlit_app.py
```

Abrir [http://localhost:8501](http://localhost:8501)

### OpenSEO *(opcional)*

```bash
# 1. Asegúrate de tener Docker Desktop abierto
"C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 2. Levantar el contenedor
docker compose --env-file .env -f ../open-seo/compose.yaml up -d

# 3. Verificar
docker ps --filter name=open-seo
curl http://localhost:3001   # debe responder HTML

# 4. Detener cuando no se use
docker compose -f ../open-seo/compose.yaml down
```

> ⚠️ La primera ejecución descarga ~758 MB y compila Vite + TypeScript (~60-80s).

---

## 🎯 Ejemplos de consultas

| Consulta | Herramienta | Resultado |
|---|---|---|
| *"Verifica si 'beneficios SEO' tiene AI Overview"* | AI Overview | Presencia de IA y fuentes |
| *"Analiza la estructura de nike.com"* | Wigolo fetch + extract | Headings, meta, schema |
| *"Analiza la velocidad de nike.com"* | PageSpeed Insights | Score, LCP, CLS, TTFB |
| *"Valida los sitemaps de nike.com"* | Validador | robots.txt + sitemap XML |
| *"Encuentra sitios similares a databiq.com para guest posting"* | Wigolo find_similar | Top 10 prospectos con detalles editoriales |
| *"Busca información sobre SEO ecommerce 2026"* | Wigolo search | Resultados web |
| *"Investigación de mercado BI en Colombia"* | Wigolo research | Reporte con fuentes |
| *"Investiga keywords para cafetería online"* | OpenSEO | Volumen, dificultad, CPC |
| *"Valida el llms.txt de anthropic.com"* | geo_llms_txt | Existe, secciones, URLs, sugerencias |
| *"¿Databiq es citado por ChatGPT y Perplexity?"* | geo_citation_check | Citation Score por plataforma |
| *"Audita nike.com para GEO"* | geo_content_audit | Score 0-100 + recomendaciones |
| *"Compara Anthropic vs OpenAI en IA"* | geo_share_of_voice | Ranking, lider, gaps competitivos |

---

## 🗺️ Roadmap
| **1.1** | 🚦 PageSpeed Insights | ✅ Completado |
| **1.2** | 🕸️ Validador de sitemaps | ✅ Completado |
| **1.3** | 🔍 Auditoria on-page (57 reglas) | 📋 Pendiente |
| **2.1** | 🧬 Analizador TF-IDF de contenido | 📋 Pendiente |
| **4.3** | 📤 Exportacion a Excel | ✅ Completado |
| **4.4** | 🔗 Prospector de link building | ✅ Completado |
| **5.1** | 📊 Dashboard de KPIs | ✅ Completado |
| **5.2** | 💾 Persistencia de sesiones | 📋 Pendiente |
| **5.4** | 🌍 AI Overviews / SGE | ✅ Completado |
| **6.1** | 🧪 Suite de tests (52 tests) | ✅ Completado |
| **8.1** | 🤖 Validador llms.txt | ✅ Completado |
| **8.2** | 🔍 Detector citas IA (6 plataformas) | ✅ Completado |
| **8.3** | 📋 Auditoria contenido GEO | ✅ Completado |
| **8.4** | 🏆 Share of Voice en IA | ✅ Completado |

---

## 📄 Licencia

MIT © 2026 Edwin Quintero Alzate

---

## 👤 Desarrollador

**Edwin Quintero Alzate** — DATABiQ

| | |
|---|---|
| 📧 | [databiq29@gmail.com](mailto:databiq29@gmail.com) |
| 🔗 | [linkedin.com/in/edwinquintero0329](https://www.linkedin.com/in/edwinquintero0329/) |
| 🌐 | [databiq.com](https://www.databiq.com) |
| 🏢 | DATABiQ — Business Intelligence & Ciencia de Datos |

---

## 🤝 Contribuciones

¿Ideas, bugs o mejoras? Abre un [issue](https://github.com/every-app/open-seo/issues) o escribe al desarrollador.

---

## ⚠️ Solución de problemas

| Problema | Solución |
|---|---|
| Wigolo no conecta | `npx wigolo doctor` — Node ≥ 20 |
| OpenSEO no conecta | Abrir Docker Desktop, luego `docker compose up -d` |
| OpenSEO build lento | Primera vez: ~60-80s (Vite + TypeScript). Normal. |
| PageSpeed error 400 | Verificar `GOOGLE_PAGESPEED_API_KEY` en `.env` |
| DeepSeek error 401 | Verificar `DEEPSEEK_API_KEY` en `.env` |
| ModuleNotFoundError: src | Ejecutar desde la carpeta `SEO_Agent/` |
| Puerto 8501 en uso | `streamlit run streamlit_app.py --server.port 8502` |

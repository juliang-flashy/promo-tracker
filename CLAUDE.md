# CLAUDE.md — Promo Tracker · Flashy Intel Competitiva

> **Para la jefa:** Clona el repo, sigue los pasos de Setup y ya tienes el dashboard funcionando. Todo corre con Claude Code — no necesitas API key adicional.

---

## ¿Qué es este proyecto?

Dashboard de inteligencia competitiva que monitorea promociones y campañas de **84 marcas** de moda y belleza (internacionales + 13 nacionales colombianas).

- **Scraper:** visita cada marca con Playwright (Chrome real), toma screenshots y los analiza visualmente con Claude
- **Dashboard:** muestra feed de promos, fichas de marcas, tendencias y — lo más importante — la pestaña **Asesor Flashy** con ideas de campañas personalizadas
- **API:** FastAPI sirve los datos al dashboard en tiempo real

---

## Setup desde cero (primera vez)

### 1. Clonar el repo
```bash
git clone https://github.com/juliang-flashy/promo-tracker.git
cd promo-tracker
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 3. Levantar la API
```bash
uvicorn api.main:app --reload --port 8000
```
Abre el navegador en **http://localhost:8000** — verás el dashboard completo.

### 4. Correr el scraper (actualiza los datos)
En otra terminal (con el venv activo):
```bash
# Probar con 3 marcas primero:
python scraper/scrape_raw.py "Flashy" "Koaj" "Nafnaf"

# Después usar el skill /scrapebrands en Claude Code para analizar los screenshots
```

---

## Cómo usar el Asesor de Campañas con Claude Code

El skill `/scrapebrands` hace todo el análisis visual:

1. Abre Claude Code en la carpeta del proyecto
2. Escribe: `/scrapebrands`
3. Claude scrapea las marcas, lee los screenshots y actualiza `data/promos.json`
4. El dashboard se actualiza automáticamente (la API sirve el JSON)

Para pedir ideas de campañas para Flashy:
- Ve a la pestaña **"Asesor Flashy ✨"** en el sidebar del dashboard
- O dile a Claude: *"Dame ideas de campañas para Flashy basadas en lo que está haciendo la competencia esta semana"*

---

## Estructura del proyecto

```
promo-tracker/
├── .claude/
│   └── commands/
│       └── scrapebrands.md   ← skill que activa el análisis completo
├── scraper/
│   ├── scrape_raw.py         ← toma screenshots con Playwright (sin API)
│   ├── agent.py              ← versión alternativa con Anthropic API
│   ├── scheduler.py          ← corre diario a las 8am
│   └── brands_config.json    ← 84 marcas con URLs
├── api/
│   └── main.py               ← FastAPI: /promos /brands /stats
├── dashboard/
│   └── index.html            ← dashboard completo (se abre en el browser)
├── data/
│   └── promos.json           ← datos de campañas (generado por el scraper)
├── screenshots/              ← capturas del scraper (ignoradas por git)
├── requirements.txt
├── README.md
└── CLAUDE.md                 ← este archivo
```

---

## Pestañas del dashboard

| Pestaña | Qué muestra |
|---------|-------------|
| Feed de promociones | Todas las campañas activas con filtros |
| Tendencias | Gráficas de tipos, canales y mapa de calor |
| Fichas de marcas | Tarjeta por cada una de las 84 marcas |
| **Asesor Flashy ✨** | **Ideas de campañas para Flashy basadas en la competencia** |

---

## Marcas monitoreadas

**Nacionales (13):** Flashy, Koaj, Tennis, Nafnaf, Karibik, Gef, True, Mattelsa, Navissi, Ela, Color Blue, Strada Brand, Seven Seven

**Internacionales (71):** Zara, Mango, Dissh, Meshki, Na-Kd, Loavies, Tiger Mist, Micas, Edikted, Miss Lola, Lioness, Reformation, Sandro, Maje, Aritzia, Ba&sh, Anine Bing, LoveShackFancy, Gap, Abercrombie, Hollister, American Eagle, Showpo, Rhode, Gisou, Byoma, Touchland, Kosas, Poppi, y más...

---

## Marcas que bloquean el scraper

Estas usan Cloudflare/Akamai enterprise — no se pueden scrapear sin proxy:
Zara, Mango, Sezane, Urban Outfitters, Free People

---

## Stack tecnológico

- **Frontend:** HTML + CSS + JS vanilla + Chart.js
- **Scraper:** Python + Playwright (Chromium)
- **Análisis visual:** Claude Code (visión de screenshots)
- **Backend:** FastAPI + uvicorn
- **Datos:** JSON local (`data/promos.json`)

---

## Notas

- `data/` y `screenshots/` están en `.gitignore` — cada quien genera sus propios datos corriendo el scraper
- El dashboard funciona abriendo `dashboard/index.html` directamente en el browser (sin backend, con datos del último scrape)
- Para actualizar datos diariamente: `python scraper/scheduler.py` (corre a las 8am automáticamente)

# Intel Competitiva 🔍

Monitor automático de promociones y campañas de 83 marcas de moda y belleza.

---

## Estructura del proyecto

```
competitive-intel/
├── scraper/
│   ├── agent.py            ← agente principal (Playwright + Claude API)
│   ├── scheduler.py        ← corre el scraper todos los días a las 8am
│   └── brands_config.json  ← 83 marcas con URLs y selectores
├── processor/              ← (próximamente: clasificador y vector store)
├── api/
│   └── main.py             ← FastAPI que sirve datos al dashboard
├── dashboard/
│   └── index.html          ← dashboard visual
├── screenshots/            ← capturas guardadas automáticamente
├── data/
│   └── promos.json         ← base de datos local de promociones
└── requirements.txt
```

---

## Setup inicial (una sola vez)

### 1. Crea el entorno virtual

```bash
cd competitive-intel
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 2. Instala dependencias

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configura tu API key de Anthropic

```bash
# Mac/Linux:
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (PowerShell):
$env:ANTHROPIC_API_KEY="sk-ant-..."

# O crea un archivo .env en la raíz:
echo ANTHROPIC_API_KEY=sk-ant-... > .env
```

> Consigue tu API key en: https://console.anthropic.com/

---

## Uso

### Scrapear todas las marcas ahora

```bash
python scraper/agent.py
```

### Scrapear solo marcas específicas

```bash
python scraper/agent.py "Zara" "Mango" "Koaj"
```

### Activar el scheduler (corre todos los días a las 8am)

```bash
python scraper/scheduler.py
```

### Correr el scheduler una sola vez inmediatamente

```bash
python scraper/scheduler.py --now
```

---

## Levantar la API

```bash
uvicorn api.main:app --reload --port 8000
```

La API queda disponible en: http://localhost:8000

Endpoints principales:
- `GET /promos` → lista de promos (filtra con ?brand=Zara&region=nacional)
- `GET /brands` → todas las marcas con estadísticas
- `GET /stats`  → resumen global
- `GET /screenshots/{archivo.png}` → sirve las capturas

---

## Conectar el dashboard a la API real

En `dashboard/index.html`, reemplaza la sección de mock data:

```javascript
// ANTES (mock data):
const PROMOS = [ ... ];

// DESPUÉS (datos reales):
const response = await fetch('http://localhost:8000/promos');
const { data: PROMOS } = await response.json();
```

---

## Notas importantes

### Instagram
El scraper guarda la URL del perfil de Instagram de cada marca pero **no scrapea
las imágenes directamente** — Instagram bloquea el scraping agresivamente.
Para capturar posts de Instagram se necesita la **Instagram Basic Display API**
(requiere cuenta de desarrollador en Meta).

### Anti-bloqueo
El agente usa:
- User-agent de Chrome real
- Espera aleatoria entre páginas
- Cierre automático de pop-ups de cookies
- Máximo 3 marcas en paralelo

Si algunas marcas bloquean el scraper, se puede añadir un proxy rotativo en
`agent.py` pasando `proxy={"server": "..."}` al `browser.new_context()`.

### Costos de Claude API
Cada marca procesa ~80KB de HTML. Con 83 marcas y Claude Sonnet:
- ~6.6M tokens de entrada por corrida completa
- Costo aproximado: ~$2–4 USD por corrida diaria
- Para reducir costos: usa `brands_filter` para scrapear solo marcas prioritarias

---

## Próximos pasos

- [ ] Processor: clasificador semántico con embeddings
- [ ] Vector store: búsqueda semántica de campañas similares
- [ ] Asesor IA: recomendaciones de campaña para tu negocio
- [ ] Alertas: notificación cuando una marca lanza nueva campaña

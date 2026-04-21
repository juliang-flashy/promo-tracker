"""
competitive-intel/scraper/agent.py
-----------------------------------
Scraper agent que visita cada marca, extrae promociones
y toma screenshots del banner/sale page.

Requiere:
    pip install playwright anthropic aiohttp aiofiles
    playwright install chromium
"""

import asyncio
import json
import os
import re
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from playwright.async_api import async_playwright, Page, BrowserContext

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
DATA_DIR    = ROOT / "data"
SHOTS_DIR   = ROOT / "screenshots"
CONFIG_FILE = Path(__file__).parent / "brands_config.json"

DATA_DIR.mkdir(exist_ok=True)
SHOTS_DIR.mkdir(exist_ok=True)

# ── Anthropic client ────────────────────────────────────────────────────────
client = Anthropic()

# ── Helpers ─────────────────────────────────────────────────────────────────
def slug(text: str) -> str:
    """brand name → safe filename slug"""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def today_str() -> str:
    return datetime.now().strftime("%Y%m%d")


def load_existing_data() -> list[dict]:
    path = DATA_DIR / "promos.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_data(promos: list[dict]) -> None:
    path = DATA_DIR / "promos.json"
    path.write_text(json.dumps(promos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ Guardado {len(promos)} promos en {path}")


# ── Screenshot ───────────────────────────────────────────────────────────────
async def take_screenshot(page: Page, brand_name: str, source: str) -> Optional[str]:
    """
    Toma screenshot de la página actual.
    Retorna la ruta relativa del archivo guardado (desde ROOT).
    """
    try:
        filename = f"{slug(brand_name)}_{source}_{today_str()}.png"
        filepath = SHOTS_DIR / filename
        await page.screenshot(path=str(filepath), full_page=False, timeout=10_000)
        rel = str(filepath.relative_to(ROOT))
        print(f"    📸 Screenshot guardado: {rel}")
        return rel
    except Exception as e:
        print(f"    ⚠️  Screenshot falló: {e}")
        return None


# ── Claude extractor ─────────────────────────────────────────────────────────
EXTRACTION_PROMPT = """
Analiza el contenido HTML de esta página de una marca de moda/belleza.
Extrae TODAS las promociones, campañas o descuentos activos que encuentres.

Para cada promoción encontrada, devuelve un objeto JSON con estos campos:
- type: "descuento" | "flash" | "lanzamiento" | "coleccion" | "blackfriday" | "otro"
- discount_pct: número entero del porcentaje de descuento (0 si no aplica)
- copy: texto exacto del mensaje/copy de la campaña (máximo 120 caracteres)
- channel: "web" (siempre web para esta fuente)
- promo_url: URL específica de la promoción si la encuentras, si no null

Responde SOLO con un array JSON válido. Sin explicaciones, sin markdown.
Ejemplo: [{"type":"descuento","discount_pct":30,"copy":"30% OFF en toda la tienda este fin de semana","channel":"web","promo_url":null}]

Si no encuentras ninguna promoción, responde: []
"""

async def extract_promos_with_claude(html: str, brand_name: str, page_url: str) -> list[dict]:
    """Llama a Claude API con el HTML para extraer promociones estructuradas."""
    # Truncamos el HTML para no exceder el contexto (primeros 80k chars son suficientes)
    html_truncated = html[:80_000]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\nMarca: {brand_name}\nURL: {page_url}\n\nHTML:\n{html_truncated}"
            }]
        )
        raw = response.content[0].text.strip()
        # Limpia posibles backticks de markdown
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"    ⚠️  Claude retornó JSON inválido: {e}")
        return []
    except Exception as e:
        print(f"    ⚠️  Error llamando a Claude: {e}")
        return []


# ── Per-brand scraper ────────────────────────────────────────────────────────
async def scrape_brand(brand: dict, context: BrowserContext) -> list[dict]:
    """
    Visita la URL web de la marca, toma screenshot y extrae promociones.
    Retorna lista de promos encontradas.
    """
    name     = brand["name"]
    web_url  = brand["urls"].get("web")
    ig_url   = brand["urls"].get("instagram")
    results  = []

    if not web_url:
        print(f"  ⏩ {name}: sin URL web configurada")
        return results

    print(f"\n🔍 Scrapeando: {name}")
    page = await context.new_page()

    try:
        # ── 1. Visita la página web ──────────────────────────────────────
        print(f"  🌐 {web_url}")
        await page.goto(web_url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(2_500)   # espera JS dinámico

        # Cierra posibles pop-ups de cookies / newsletter
        for selector in [
            "button[id*='accept']", "button[class*='accept']",
            "button[id*='close']",  "button[class*='close']",
            "[aria-label='Close']", "[aria-label='close']",
            ".modal-close", "#onetrust-accept-btn-handler",
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=1_000):
                    await btn.click(timeout=1_000)
                    await page.wait_for_timeout(500)
            except Exception:
                pass

        # Screenshot de la web
        shot_web = await take_screenshot(page, name, "web")

        # HTML para Claude
        html = await page.content()
        promos_raw = await extract_promos_with_claude(html, name, web_url)
        print(f"  🤖 Claude encontró {len(promos_raw)} promo(s) en la web")

        for p in promos_raw:
            results.append({
                "id":           f"{slug(name)}_{today_str()}_{hashlib.md5(p.get('copy','').encode()).hexdigest()[:6]}",
                "brand":        name,
                "region":       brand["region"],
                "cat":          brand["category"],
                "type":         p.get("type", "otro"),
                "discount":     int(p.get("discount_pct", 0)),
                "desc":         p.get("copy", "")[:120],
                "channel":      "Web",
                "date":         datetime.now().strftime("%d %b %Y"),
                "url":          p.get("promo_url") or web_url,
                "screenshot":   shot_web,
                "source":       "web",
                "scraped_at":   datetime.now().isoformat(),
            })

        # ── 2. Instagram (solo guardamos URL del perfil, no scrapeamos) ──
        # Instagram bloquea scraping. El campo instagram_url queda guardado
        # para abrirlo manualmente o integrarlo con la API oficial después.
        if ig_url:
            for r in results:
                r["instagram_url"] = ig_url

    except Exception as e:
        print(f"  ❌ Error scrapeando {name}: {e}")

    finally:
        await page.close()

    return results


# ── Main runner ───────────────────────────────────────────────────────────────
async def run(brands_filter: Optional[list[str]] = None, max_concurrent: int = 3):
    """
    Ejecuta el scraper para todas las marcas (o un subconjunto).

    Args:
        brands_filter: lista de nombres de marcas a scrapear.
                       None = todas.
        max_concurrent: cuántas marcas en paralelo (cuidado con el rate limiting).
    """
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    brands = config["brands"]

    if brands_filter:
        brands = [b for b in brands if b["name"] in brands_filter]

    print(f"\n{'='*55}")
    print(f"  Intel Competitiva — Scraper")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  {len(brands)} marcas")
    print(f"{'='*55}")

    all_promos = load_existing_data()
    # Elimina entradas de hoy para re-scraping limpio
    today = today_str()
    all_promos = [p for p in all_promos if today not in p.get("scraped_at", "")]

    semaphore = asyncio.Semaphore(max_concurrent)
    new_promos: list[dict] = []

    async def bounded_scrape(brand: dict, context: BrowserContext):
        async with semaphore:
            return await scrape_brand(brand, context)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="es-CO",
        )

        tasks = [bounded_scrape(b, context) for b in brands]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, list):
                new_promos.extend(r)

        await browser.close()

    all_promos.extend(new_promos)
    # Ordena por fecha descendente
    all_promos.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)
    save_data(all_promos)

    print(f"\n{'='*55}")
    print(f"  ✅ Listo. {len(new_promos)} nuevas promos detectadas hoy.")
    print(f"  📁 Datos: {DATA_DIR / 'promos.json'}")
    print(f"  📸 Screenshots: {SHOTS_DIR}/")
    print(f"{'='*55}\n")

    return new_promos


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    # Uso: python agent.py                  → scrapea todas las marcas
    # Uso: python agent.py "Zara" "Mango"   → solo esas marcas
    filter_list = sys.argv[1:] or None
    asyncio.run(run(brands_filter=filter_list))

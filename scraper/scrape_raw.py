"""
Scrapea las marcas con Playwright y guarda texto crudo + screenshots.
No llama a ninguna API externa. Claude Code analiza el resultado despues.

Uso:
  python scraper/scrape_raw.py               -> todas las marcas
  python scraper/scrape_raw.py Flashy Nafnaf -> marcas especificas
"""
import sys, io, json, time, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
from datetime import datetime

CONFIG_PATH  = "C:/Users/ASUS/Desktop/competitive-intel/scraper/brands_config.json"
OUTPUT_PATH  = "C:/Users/ASUS/Desktop/competitive-intel/data/raw_scrape.json"
SCREENSHOTS  = "C:/Users/ASUS/Desktop/competitive-intel/screenshots"

SKIP_BRANDS = {"Zara", "Mango", "& Other Stories", "Madewell", "J.Crew", "Daise"}
JS_HEAVY    = {"Sezane", "Urban Outfitters", "Free People", "Nude Project"}

os.makedirs(SCREENSHOTS, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(CONFIG_PATH, encoding="utf-8") as f:
    config = json.load(f)

# Filtrar por nombres si se pasan como argumentos
nombres_filtro = [a for a in sys.argv[1:]]
marcas = config["brands"]
if nombres_filtro:
    marcas = [b for b in marcas if b["name"] in nombres_filtro]
else:
    marcas = [b for b in marcas if b["name"] not in SKIP_BRANDS]

print(f"Scrapeando {len(marcas)} marcas...\n")

resultados = []

def limpiar_texto(texto):
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    # Eliminar lineas duplicadas consecutivas
    vistas = []
    for l in lineas:
        if not vistas or l != vistas[-1]:
            vistas.append(l)
    return vistas

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900},
        locale="es-CO",
    )
    page = context.new_page()

    for brand in marcas:
        nombre = brand["name"]
        url    = brand["urls"]["web"]
        espera = 5 if nombre in JS_HEAVY else 3

        print(f"  -> {nombre} ({url})")
        try:
            page.goto(url, timeout=30000, wait_until="load")
            time.sleep(espera)

            # Cerrar popups comunes
            for sel in ["#onetrust-accept-btn-handler", ".modal-close", "[aria-label='Close']",
                        ".popup-close", ".cookie-accept", "button:has-text('Accept')",
                        "button:has-text('Aceptar')", "button:has-text('Accept all')"]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=800):
                        btn.click()
                        time.sleep(0.5)
                except:
                    pass

            # Screenshot
            screenshot_file = f"{SCREENSHOTS}/{re.sub(r'[^a-z0-9]', '_', nombre.lower())}.png"
            page.screenshot(path=screenshot_file, full_page=False)

            # Texto visible
            texto = page.inner_text("body")
            lineas = limpiar_texto(texto)

            resultado = {
                "marca": nombre,
                "region": brand["region"],
                "categoria": brand["category"],
                "url": url,
                "fecha_scrape": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "screenshot": screenshot_file,
                "texto_lineas": lineas,
                "status": "ok"
            }
            print(f"     OK — {len(lineas)} lineas, screenshot guardado")

        except Exception as e:
            resultado = {
                "marca": nombre,
                "region": brand["region"],
                "categoria": brand["category"],
                "url": url,
                "fecha_scrape": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "screenshot": None,
                "texto_lineas": [],
                "status": "error",
                "error": str(e)[:200]
            }
            print(f"     ERROR — {str(e)[:80]}")

        resultados.append(resultado)

    browser.close()

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

ok    = sum(1 for r in resultados if r["status"] == "ok")
error = sum(1 for r in resultados if r["status"] == "error")
print(f"\nListo: {ok} OK, {error} errores")
print(f"Datos guardados en {OUTPUT_PATH}")

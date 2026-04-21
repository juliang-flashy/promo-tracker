"""
Test scraper con Playwright - visita mango.com y flashy.com.co
y extrae todo el contenido visible de la página.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright
import json
import time

MARCAS = [
    {"nombre": "Flashy",  "url": "https://www.flashy.com.co"},
    {"nombre": "Mango",   "url": "https://www.mango.com/co"},
    {"nombre": "Zara",    "url": "https://www.zara.com/co/es/"},
    {"nombre": "Nafnaf",  "url": "https://www.nafnaf.com.co"},
    {"nombre": "Koaj",    "url": "https://www.koaj.co"},
]

def scrape(page, marca):
    print(f"\n→ Visitando {marca['nombre']} ({marca['url']})")
    try:
        page.goto(marca["url"], timeout=30000, wait_until="domcontentloaded")
        time.sleep(3)  # esperar JS

        # Cerrar popups comunes
        for selector in ["button[aria-label='Close']", ".modal-close", ".popup-close",
                         "[data-testid='close']", ".close-button", "#onetrust-accept-btn-handler"]:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=1000):
                    btn.click()
                    time.sleep(1)
            except:
                pass

        # Extraer todo el texto visible
        texto = page.inner_text("body")
        # Limpiar líneas vacías
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]

        # Tomar screenshot
        screenshot_path = f"C:/Users/ASUS/Desktop/competitive-intel/screenshots/{marca['nombre'].lower()}_test.png"
        page.screenshot(path=screenshot_path, full_page=False)

        print(f"  ✅ OK — {len(lineas)} líneas de texto extraídas")
        print(f"  📸 Screenshot guardado en {screenshot_path}")
        print(f"\n  --- PRIMERAS 40 LÍNEAS ---")
        for l in lineas[:40]:
            print(f"  {l}")

        return {"marca": marca["nombre"], "url": marca["url"], "status": "ok", "lineas": lineas[:100]}

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return {"marca": marca["nombre"], "url": marca["url"], "status": "error", "error": str(e)}


def main():
    import os
    os.makedirs("C:/Users/ASUS/Desktop/competitive-intel/screenshots", exist_ok=True)

    resultados = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="es-CO",
        )
        page = context.new_page()

        for marca in MARCAS:
            resultado = scrape(page, marca)
            resultados.append(resultado)

        browser.close()

    # Resumen
    print("\n\n========== RESUMEN ==========")
    for r in resultados:
        status = "✅" if r["status"] == "ok" else "❌"
        print(f"{status} {r['marca']}: {r['status']}")

    with open("C:/Users/ASUS/Desktop/competitive-intel/test_resultado.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("\nResultados guardados en test_resultado.json")


if __name__ == "__main__":
    main()

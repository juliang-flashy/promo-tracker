import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json, time
from playwright.sync_api import sync_playwright

# Lee las marcas directo del config actualizado
with open("C:/Users/ASUS/Desktop/competitive-intel/scraper/brands_config.json", encoding="utf-8") as f:
    config = json.load(f)

MARCAS = [{"nombre": b["name"], "url": b["urls"]["web"]} for b in config["brands"]]

BLOCKED_KEYWORDS = ["access denied", "you don't have permission", "403 forbidden",
                    "enable javascript", "checking your browser", "please enable cookies",
                    "ddos protection", "cloudflare", "just a moment", "verifying you are human"]

def evaluar(texto, n_lineas):
    texto_lower = texto.lower()
    for kw in BLOCKED_KEYWORDS:
        if kw in texto_lower:
            return "BLOQUEADA", kw
    if n_lineas < 5:
        return "VACIA", "menos de 5 lineas"
    return "OK", f"{n_lineas} lineas"

def test_marca(page, marca):
    try:
        # wait_until="load" maneja redireccionamientos mejor que domcontentloaded
        page.goto(marca["url"], timeout=30000, wait_until="load")
        time.sleep(2)
        texto = page.inner_text("body")
        lineas = [l.strip() for l in texto.splitlines() if l.strip()]
        estado, detalle = evaluar(texto, len(lineas))
        print(f"  [{estado:8}] {marca['nombre']:25} — {detalle}")
        return {"nombre": marca["nombre"], "url": marca["url"], "estado": estado, "detalle": detalle, "muestra": lineas[:5]}
    except Exception as e:
        err = str(e)[:80]
        print(f"  [ERROR   ] {marca['nombre']:25} — {err}")
        return {"nombre": marca["nombre"], "url": marca["url"], "estado": "ERROR", "detalle": err}

def main():
    resultados = []
    print(f"Probando {len(MARCAS)} marcas con Playwright...\n")

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
            r = test_marca(page, marca)
            resultados.append(r)

        browser.close()

    ok    = [r for r in resultados if r["estado"] == "OK"]
    bloq  = [r for r in resultados if r["estado"] == "BLOQUEADA"]
    vacia = [r for r in resultados if r["estado"] == "VACIA"]
    error = [r for r in resultados if r["estado"] == "ERROR"]

    print(f"\n{'='*55}")
    print(f"  RESUMEN FINAL — {len(MARCAS)} marcas probadas")
    print(f"{'='*55}")
    print(f"  ACCESIBLES  : {len(ok)}")
    print(f"  BLOQUEADAS  : {len(bloq)}")
    print(f"  VACIAS/JS   : {len(vacia)}")
    print(f"  ERROR/CAIDA : {len(error)}")
    print(f"{'='*55}")

    print(f"\n--- ACCESIBLES ({len(ok)}) ---")
    for r in ok:
        print(f"  {r['nombre']}")

    print(f"\n--- BLOQUEADAS ({len(bloq)}) ---")
    for r in bloq:
        print(f"  {r['nombre']} ({r['detalle']})")

    print(f"\n--- VACIAS / SOLO JS ({len(vacia)}) ---")
    for r in vacia:
        print(f"  {r['nombre']} ({r['detalle']})")

    print(f"\n--- ERROR / CAIDA ({len(error)}) ---")
    for r in error:
        print(f"  {r['nombre']} — {r['detalle']}")

    with open("C:/Users/ASUS/Desktop/competitive-intel/resultado_todas.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("\nResultado guardado en resultado_todas.json")

if __name__ == "__main__":
    main()

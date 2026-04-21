"""
competitive-intel/api/main.py
-------------------------------
API que conecta el dashboard con los datos reales del scraper.

Endpoints:
    GET  /promos          → lista de promociones con filtros
    GET  /brands          → lista de marcas con estadísticas
    GET  /stats           → estadísticas globales
    GET  /screenshots/{filename}  → sirve las imágenes

Uso:
    uvicorn api.main:app --reload --port 8000
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import json

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
DATA_FILE   = ROOT / "data" / "promos.json"
SHOTS_DIR   = ROOT / "screenshots"
CONFIG_FILE = ROOT / "scraper" / "brands_config.json"
DASHBOARD   = ROOT / "dashboard" / "index.html"

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(title="Intel Competitiva API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sirve screenshots como archivos estáticos
if SHOTS_DIR.exists():
    app.mount("/screenshots", StaticFiles(directory=str(SHOTS_DIR)), name="screenshots")


# ── Helpers ────────────────────────────────────────────────────────────────
def load_promos() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []

def load_brands() -> list[dict]:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))["brands"]
    return []


# ── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    if DASHBOARD.exists():
        return FileResponse(str(DASHBOARD), media_type="text/html")
    return {"status": "ok", "message": "Intel Competitiva API"}


@app.get("/promos")
def get_promos(
    brand:    Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    type:     Optional[str] = Query(None),
    search:   Optional[str] = Query(None),
    limit:    int = Query(100, le=500),
    offset:   int = Query(0),
):
    promos = load_promos()

    if brand:
        promos = [p for p in promos if p.get("brand","").lower() == brand.lower()]
    if region:
        promos = [p for p in promos if p.get("region","") == region]
    if category:
        promos = [p for p in promos if p.get("cat","") == category]
    if type:
        promos = [p for p in promos if p.get("type","") == type]
    if search:
        s = search.lower()
        promos = [p for p in promos if s in p.get("brand","").lower() or s in p.get("desc","").lower()]

    total = len(promos)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "data": promos[offset : offset + limit],
    }


@app.get("/brands")
def get_brands(
    region:   Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    brands  = load_brands()
    promos  = load_promos()

    if region:
        brands = [b for b in brands if b.get("region") == region]
    if category:
        brands = [b for b in brands if b.get("category") == category]

    result = []
    for b in brands:
        bp = [p for p in promos if p.get("brand") == b["name"]]
        with_disc = [p for p in bp if p.get("discount", 0) > 0]
        avg_disc = (
            round(sum(p["discount"] for p in with_disc) / len(with_disc))
            if with_disc else 0
        )
        channels = list({p.get("channel","") for p in bp})
        last_promo = bp[0] if bp else None

        result.append({
            **b,
            "promo_count":   len(bp),
            "avg_discount":  avg_disc,
            "channels":      channels,
            "last_promo":    last_promo,
        })

    return result


@app.get("/stats")
def get_stats():
    promos = load_promos()
    if not promos:
        return {}

    with_disc = [p for p in promos if p.get("discount", 0) > 0]
    avg_disc  = round(sum(p["discount"] for p in with_disc) / len(with_disc)) if with_disc else 0

    type_counts = {}
    for p in promos:
        t = p.get("type", "otro")
        type_counts[t] = type_counts.get(t, 0) + 1

    channel_counts = {}
    for p in promos:
        c = p.get("channel", "")
        channel_counts[c] = channel_counts.get(c, 0) + 1

    brand_counts = {}
    for p in promos:
        b = p.get("brand", "")
        brand_counts[b] = brand_counts.get(b, 0) + 1

    most_active = max(brand_counts, key=brand_counts.get) if brand_counts else ""
    top_type    = max(type_counts,  key=type_counts.get)  if type_counts  else ""
    top_channel = max(channel_counts, key=channel_counts.get) if channel_counts else ""

    return {
        "total_promos":    len(promos),
        "active_brands":   len(brand_counts),
        "avg_discount":    avg_disc,
        "most_active_brand": most_active,
        "top_type":        top_type,
        "top_channel":     top_channel,
        "type_counts":     type_counts,
        "channel_counts":  channel_counts,
    }


@app.get("/screenshots/{filename}")
def get_screenshot(filename: str):
    path = SHOTS_DIR / filename
    if path.exists():
        return FileResponse(str(path), media_type="image/png")
    return {"error": "Screenshot no encontrado"}

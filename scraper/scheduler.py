"""
competitive-intel/scraper/scheduler.py
----------------------------------------
Corre el scraper automáticamente todos los días a la hora configurada.
Usa schedule (liviano, sin dependencias de sistema).

Uso:
    python scheduler.py              # corre en background
    python scheduler.py --now        # corre inmediatamente una vez
"""

import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

import schedule
import time

# Añade el root al path para importar agent
sys.path.insert(0, str(Path(__file__).parent))
from agent import run as run_scraper

# ── Logging ────────────────────────────────────────────────────────────────
LOG_FILE = Path(__file__).parent.parent / "data" / "scheduler.log"
LOG_FILE.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

# ── Configuración ──────────────────────────────────────────────────────────
RUN_AT        = "08:00"   # hora local de ejecución diaria
MAX_CONCURRENT = 3        # marcas en paralelo


def job():
    log.info("⏰ Iniciando scraping programado...")
    try:
        new = asyncio.run(run_scraper(max_concurrent=MAX_CONCURRENT))
        log.info(f"✅ Scraping completado. {len(new)} nuevas promos.")
    except Exception as e:
        log.error(f"❌ Error en scraping: {e}", exc_info=True)


def main():
    if "--now" in sys.argv:
        log.info("▶ Ejecución manual inmediata")
        job()
        return

    log.info(f"📅 Scheduler activo — corre todos los días a las {RUN_AT}")
    schedule.every().day.at(RUN_AT).do(job)

    # También corre al iniciar si es la primera vez del día
    last_run_file = Path(__file__).parent.parent / "data" / ".last_run"
    today = datetime.now().strftime("%Y-%m-%d")
    if not last_run_file.exists() or last_run_file.read_text().strip() != today:
        log.info("🔄 Primera ejecución del día — corriendo ahora...")
        job()
        last_run_file.write_text(today)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()

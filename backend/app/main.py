from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.manifest import build_slideshow_response
from app.scheduler import ensure_bootstrap_media, refresh_all, start_scheduler
from app.services.basemap import BUNDLED_STATES
from app.state import DataStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

store = DataStore(Path(settings.data_dir))


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bootstrap_media(store)
    store.set_revision("weather", "bootstrap")
    store.set_revision("ham", "bootstrap")
    scheduler = start_scheduler(store)
    scheduler.start()
    try:
        await refresh_all(store)
    except Exception:
        logger.exception("Initial refresh failed; serving placeholders")
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="ESP32 Weather Slideshow API", version="0.1.2", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    snap = store.snapshot()
    return {
        "status": "ok",
        "api_version": app.version,
        "spc_basemap_bundled": BUNDLED_STATES.is_file(),
        "spc_revision": store.get_revision("spc_day1_cat.jpg"),
        "last_refresh": snap.last_refresh.isoformat() if snap.last_refresh else None,
    }


@app.get("/api/v1/slideshow")
def get_slideshow():
    return build_slideshow_response(store)


@app.get("/media/{filename}")
def get_media(filename: str):
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.endswith(".jpg"):
        raise HTTPException(status_code=404, detail="Not found")
    path = store.media_path(filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="image/jpeg")

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.models.slideshow import AlertItem, HamSnapshot, WeatherSnapshot


@dataclass
class CacheState:
    weather: WeatherSnapshot | None = None
    ham: HamSnapshot | None = None
    alerts: list[AlertItem] = field(default_factory=list)
    media_revisions: dict[str, str] = field(default_factory=dict)
    last_refresh: datetime | None = None


class DataStore:
    """Thread-safe in-memory view of cached JSON + on-disk media."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.media_dir = data_dir / "media"
        self.cache_dir = data_dir / "cache"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.state = CacheState()

    def save_json_cache(self, name: str, payload: dict) -> None:
        path = self.cache_dir / f"{name}.json"
        path.write_text(json.dumps(payload, default=str), encoding="utf-8")

    def media_path(self, filename: str) -> Path:
        return self.media_dir / filename

    def set_revision(self, media_name: str, revision: str) -> None:
        with self._lock:
            self.state.media_revisions[media_name] = revision

    def get_revision(self, media_name: str) -> str:
        with self._lock:
            return self.state.media_revisions.get(media_name, "0")

    def snapshot(self) -> CacheState:
        with self._lock:
            return CacheState(
                weather=self.state.weather,
                ham=self.state.ham,
                alerts=list(self.state.alerts),
                media_revisions=dict(self.state.media_revisions),
                last_refresh=self.state.last_refresh,
            )

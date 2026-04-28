from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    fetched_at: str
    payload: dict[str, Any]


class JsonCache:
    def __init__(self, cache_file: Path) -> None:
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.cache_file.exists():
            self.cache_file.write_text("{}", encoding="utf-8")

    def get(self, key: str, ttl_minutes: int) -> dict[str, Any] | None:
        data = self._read_all()
        raw = data.get(key)
        if not raw:
            return None
        fetched_at = raw.get("fetched_at")
        if not fetched_at:
            return None
        try:
            stamp = datetime.fromisoformat(fetched_at)
        except ValueError:
            return None
        if datetime.now(UTC) - stamp > timedelta(minutes=ttl_minutes):
            return None
        return raw.get("payload")

    def set(self, key: str, payload: dict[str, Any]) -> None:
        data = self._read_all()
        entry = CacheEntry(
            fetched_at=datetime.now(UTC).isoformat(),
            payload=payload,
        )
        data[key] = asdict(entry)
        self.cache_file.write_text(json.dumps(data), encoding="utf-8")

    def _read_all(self) -> dict[str, Any]:
        try:
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

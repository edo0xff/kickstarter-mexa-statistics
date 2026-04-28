from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests


FX_URL = "https://open.er-api.com/v6/latest/USD"


class FxProvider:
    def __init__(self, cache_file: Path, ttl_hours: int = 24, timeout_s: int = 15) -> None:
        self.cache_file = cache_file
        self.ttl_hours = ttl_hours
        self.timeout_s = timeout_s
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

    def get_rates(self) -> dict[str, float]:
        cached = self._read_cache()
        if cached is not None:
            return cached

        resp = requests.get(FX_URL, timeout=self.timeout_s)
        resp.raise_for_status()
        payload = resp.json()
        rates = payload.get("rates")
        if not isinstance(rates, dict):
            raise RuntimeError("No se pudieron obtener tasas FX.")

        clean_rates = {k.upper(): float(v) for k, v in rates.items()}
        self._write_cache(clean_rates)
        return clean_rates

    def to_usd(self, amount: float, currency: str, rates: dict[str, float]) -> float:
        cur = currency.upper()
        if cur == "USD":
            return amount
        rate = rates.get(cur)
        if not rate:
            return 0.0
        return amount / rate

    def usd_to_mxn(self, usd_amount: float, rates: dict[str, float]) -> float:
        mxn = rates.get("MXN")
        if not mxn:
            return 0.0
        return usd_amount * mxn

    def _read_cache(self) -> dict[str, float] | None:
        if not self.cache_file.exists():
            return None
        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        stamp_raw = payload.get("fetched_at")
        if not isinstance(stamp_raw, str):
            return None

        try:
            stamp = datetime.fromisoformat(stamp_raw)
        except ValueError:
            return None

        if datetime.now(UTC) - stamp > timedelta(hours=self.ttl_hours):
            return None

        rates = payload.get("rates")
        if not isinstance(rates, dict):
            return None

        return {k.upper(): float(v) for k, v in rates.items()}

    def _write_cache(self, rates: dict[str, float]) -> None:
        payload: dict[str, Any] = {
            "fetched_at": datetime.now(UTC).isoformat(),
            "rates": rates,
        }
        self.cache_file.write_text(json.dumps(payload), encoding="utf-8")

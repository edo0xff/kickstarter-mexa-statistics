from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cloudscraper
import requests

from .cache import JsonCache
from .models import ProjectRecord


DISCOVER_URL = "https://www.kickstarter.com/discover/advanced.json"


class ScrapeBlockedError(RuntimeError):
    pass


@dataclass(slots=True)
class ScrapeConfig:
    max_pages: int = 5
    max_projects: int = 300
    country_code: str = "MX"
    delay_ms: int = 700
    timeout_s: int = 20
    cache_ttl_minutes: int = 120


class KickstarterDiscoverScraper:
    def __init__(self, cache_file: Path, config: ScrapeConfig) -> None:
        self.config = config
        self.cache = JsonCache(cache_file)
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        self.fallback_session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.kickstarter.com/discover",
            }
        )
        self.fallback_session.headers.update(dict(self.session.headers))

    def collect(self) -> list[ProjectRecord]:
        projects: list[ProjectRecord] = []
        seen_ids: set[int] = set()

        for page in range(1, self.config.max_pages + 1):
            payload = self._fetch_page(page)
            raw_projects = payload.get("projects") or []
            for item in raw_projects:
                record = ProjectRecord.from_discover_project(item)
                if record.project_id in seen_ids:
                    continue
                seen_ids.add(record.project_id)
                projects.append(record)
                if len(projects) >= self.config.max_projects:
                    return projects

            has_more = bool(payload.get("has_more"))
            if not has_more:
                break
            time.sleep(max(self.config.delay_ms, 0) / 1000.0)

        return projects

    def _fetch_page(self, page: int) -> dict[str, Any]:
        params = {
            "state": "successful",
            "category_id": 35,
            "sort": "most_funded",
            "country": self.config.country_code.upper(),
            "page": page,
        }
        cache_key = (
            "discover:"
            f"{page}:state=successful:category=35:sort=most_funded:country={self.config.country_code.upper()}"
        )
        cached = self.cache.get(cache_key, ttl_minutes=self.config.cache_ttl_minutes)
        if cached is not None:
            return cached

        payload = self._request_json(DISCOVER_URL, params=params)
        self.cache.set(cache_key, payload)
        return payload

    def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        attempts = 3
        backoff = 1.2
        last_status: int | None = None

        for attempt in range(1, attempts + 1):
            blocked_count = 0

            for client in (self.session, self.fallback_session):
                try:
                    resp = client.get(url, params=params, timeout=self.config.timeout_s)
                except requests.RequestException:
                    continue

                last_status = resp.status_code
                body = resp.text.lower()

                if resp.status_code in (403, 429) or "just a moment" in body or "cf_chl" in body:
                    blocked_count += 1
                    continue

                if resp.ok:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        raise RuntimeError("Respuesta no JSON desde Kickstarter.") from exc

            if blocked_count >= 2 and attempt >= attempts:
                raise ScrapeBlockedError(
                    "Kickstarter bloqueo las solicitudes (403/429 o challenge anti-bot). "
                    "Incrementa --delay-ms y reduce --max-pages."
                )

            if attempt >= attempts:
                status_repr = last_status if last_status is not None else "N/A"
                raise RuntimeError(f"Error HTTP {status_repr} en {url}")

            time.sleep(backoff * attempt)

        raise RuntimeError("No se pudo completar la solicitud JSON.")

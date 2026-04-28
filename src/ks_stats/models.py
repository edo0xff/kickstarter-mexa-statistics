from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import dataclass
from typing import Any


def _pick_image_url(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Prefer medium-size image when available.
        for key in ("med", "medium", "full", "small", "thumb", "little"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
    return ""


def _normalize_epoch_seconds(value: Any) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        epoch = float(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            epoch = float(stripped)
        except ValueError:
            return None
    else:
        return None

    # Handle millisecond timestamps defensively.
    if abs(epoch) > 10_000_000_000:
        epoch = epoch / 1000.0

    try:
        return int(epoch)
    except (OverflowError, ValueError):
        return None


def _parse_kickstarter_datetime(value: Any) -> tuple[str | None, int | None]:
    if value is None:
        return None, None

    epoch = _normalize_epoch_seconds(value)
    if epoch is not None:
        try:
            dt = datetime.fromtimestamp(epoch, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None, None
        return dt.isoformat().replace("+00:00", "Z"), epoch

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None, None
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None, None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.isoformat().replace("+00:00", "Z"), int(dt.timestamp())

    return None, None


@dataclass(slots=True)
class ProjectRecord:
    project_id: int
    name: str
    creator_name: str
    creator_slug: str
    state: str
    category_name: str
    category_slug: str
    location_country: str
    location_display: str
    pledged_original: float
    currency: str
    usd_pledged: float
    project_url: str
    launched_at_iso: str | None = None
    launched_at_epoch: int | None = None
    deadline_iso: str | None = None
    deadline_epoch: int | None = None
    updated_at_iso: str | None = None
    updated_at_epoch: int | None = None
    project_image_url: str = ""
    creator_photo_url: str = ""

    @classmethod
    def from_discover_project(cls, data: dict[str, Any]) -> "ProjectRecord":
        creator = data.get("creator") or {}
        category = data.get("category") or {}
        location = data.get("location") or {}
        urls = data.get("urls") or {}
        web_urls = urls.get("web") or {}
        photo = data.get("photo")
        creator_photo = creator.get("avatar")
        launched_at_iso, launched_at_epoch = _parse_kickstarter_datetime(data.get("launched_at"))
        deadline_iso, deadline_epoch = _parse_kickstarter_datetime(data.get("deadline"))
        updated_at_iso, updated_at_epoch = _parse_kickstarter_datetime(data.get("updated_at"))

        return cls(
            project_id=int(data.get("id", 0)),
            name=str(data.get("name") or ""),
            creator_name=str(creator.get("name") or "Unknown"),
            creator_slug=str(creator.get("slug") or ""),
            state=str(data.get("state") or ""),
            category_name=str(category.get("name") or ""),
            category_slug=str(category.get("slug") or ""),
            location_country=str(location.get("country") or ""),
            location_display=str(location.get("displayable_name") or "Unknown"),
            pledged_original=float(data.get("pledged") or 0.0),
            currency=str(data.get("currency") or ""),
            usd_pledged=float(data.get("usd_pledged") or 0.0),
            project_url=str(web_urls.get("project") or ""),
            launched_at_iso=launched_at_iso,
            launched_at_epoch=launched_at_epoch,
            deadline_iso=deadline_iso,
            deadline_epoch=deadline_epoch,
            updated_at_iso=updated_at_iso,
            updated_at_epoch=updated_at_epoch,
            project_image_url=_pick_image_url(photo),
            creator_photo_url=_pick_image_url(creator_photo),
        )

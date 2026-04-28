from __future__ import annotations

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
            project_image_url=_pick_image_url(photo),
            creator_photo_url=_pick_image_url(creator_photo),
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from .models import ProjectRecord


@dataclass(slots=True)
class StatsContext:
    top_n: int
    country_code: str = "MX"


class Statistic(Protocol):
    key: str
    title: str

    def compute(self, records: list[ProjectRecord], ctx: StatsContext) -> list[dict[str, Any]]:
        ...


STAT_REGISTRY: list[Statistic] = []
TStat = TypeVar("TStat", bound=type)


def register_stat(stat_cls: TStat) -> TStat:
    STAT_REGISTRY.append(stat_cls())
    return stat_cls


def filter_target_scope(records: list[ProjectRecord], country_code: str = "MX") -> list[ProjectRecord]:
    cc = country_code.upper()
    return [
        r
        for r in records
        if r.state.lower() == "successful"
        and r.location_country.upper() == cc
        and r.category_slug.lower() == "games/video games"
    ]


@register_stat
class TopProjectsMX:
    key = "top_projects_mx"
    title = "Top proyectos de Video Games (MX) por recaudacion"

    def compute(self, records: list[ProjectRecord], ctx: StatsContext) -> list[dict[str, Any]]:
        scope = filter_target_scope(records, country_code=ctx.country_code)
        scope.sort(key=lambda r: r.usd_pledged, reverse=True)
        rows: list[dict[str, Any]] = []
        for rec in scope[: ctx.top_n]:
            rows.append(
                {
                    "name": rec.name,
                    "creator": rec.creator_name,
                    "country": rec.location_country,
                    "location": rec.location_display,
                    "currency": rec.currency,
                    "pledged_original": rec.pledged_original,
                    "usd": rec.usd_pledged,
                    "url": rec.project_url,
                    "project_image_url": rec.project_image_url,
                }
            )
        return rows


@register_stat
class TopCreatorsMX:
    key = "top_creators_mx"
    title = "Top creadores/estudios (MX) por recaudacion acumulada"

    def compute(self, records: list[ProjectRecord], ctx: StatsContext) -> list[dict[str, Any]]:
        scope = filter_target_scope(records, country_code=ctx.country_code)
        acc: dict[str, dict[str, Any]] = {}
        for rec in scope:
            key = rec.creator_name.strip().lower()
            if key not in acc:
                acc[key] = {
                    "creator": rec.creator_name,
                    "projects": 0,
                    "usd_total": 0.0,
                    "mxn_total": 0.0,
                    "creator_url": f"https://www.kickstarter.com/profile/{rec.creator_slug}" if rec.creator_slug else "",
                    "creator_photo_url": rec.creator_photo_url,
                }
            acc[key]["projects"] += 1
            acc[key]["usd_total"] += rec.usd_pledged

        rows = list(acc.values())
        rows.sort(key=lambda r: r["usd_total"], reverse=True)
        return rows[: ctx.top_n]


def compute_all(
    records: list[ProjectRecord],
    top_n: int,
    country_code: str = "MX",
) -> dict[str, list[dict[str, Any]]]:
    ctx = StatsContext(top_n=top_n, country_code=country_code)
    out: dict[str, list[dict[str, Any]]] = {}
    for stat in STAT_REGISTRY:
        out[stat.key] = stat.compute(records, ctx)
    return out

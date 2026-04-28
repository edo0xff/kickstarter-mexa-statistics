from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from .models import ProjectRecord


@dataclass(slots=True)
class StatsContext:
    top_n: int
    country_code: str = "MX"
    rates: dict[str, float] | None = None


def pledged_to_mxn(pledged_original: float, currency: str, rates: dict[str, float] | None) -> float:
    if pledged_original <= 0:
        return 0.0

    cur = currency.upper()
    fx = rates or {}

    if cur == "MXN":
        return pledged_original

    mxn_rate = float(fx.get("MXN") or 0.0)
    if mxn_rate <= 0:
        return 0.0

    if cur == "USD":
        return pledged_original * mxn_rate

    cur_rate = float(fx.get(cur) or 0.0)
    if cur_rate <= 0:
        return 0.0

    usd_amount = pledged_original / cur_rate
    return usd_amount * mxn_rate


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
        scope.sort(
            key=lambda r: pledged_to_mxn(r.pledged_original, r.currency, ctx.rates),
            reverse=True,
        )
        rows: list[dict[str, Any]] = []
        for rec in scope[: ctx.top_n]:
            pledged_mxn = pledged_to_mxn(rec.pledged_original, rec.currency, ctx.rates)
            rows.append(
                {
                    "name": rec.name,
                    "creator": rec.creator_name,
                    "country": rec.location_country,
                    "location": rec.location_display,
                    "currency": rec.currency,
                    "pledged_original": rec.pledged_original,
                    "usd": rec.usd_pledged,
                    "mxn": pledged_mxn,
                    "url": rec.project_url,
                    "launched_at_iso": rec.launched_at_iso,
                    "launched_at_epoch": rec.launched_at_epoch,
                    "deadline_iso": rec.deadline_iso,
                    "deadline_epoch": rec.deadline_epoch,
                    "updated_at_iso": rec.updated_at_iso,
                    "updated_at_epoch": rec.updated_at_epoch,
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
            acc[key]["mxn_total"] += pledged_to_mxn(rec.pledged_original, rec.currency, ctx.rates)

        rows = list(acc.values())
        rows.sort(key=lambda r: r["mxn_total"], reverse=True)
        return rows[: ctx.top_n]


def compute_all(
    records: list[ProjectRecord],
    top_n: int,
    country_code: str = "MX",
    rates: dict[str, float] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    ctx = StatsContext(top_n=top_n, country_code=country_code, rates=rates)
    out: dict[str, list[dict[str, Any]]] = {}
    for stat in STAT_REGISTRY:
        out[stat.key] = stat.compute(records, ctx)
    return out

from ks_stats.models import ProjectRecord
from ks_stats.stats import TopCreatorsMX, TopProjectsMX, StatsContext, filter_target_scope


def _record(
    pid: int,
    creator: str,
    usd: float,
    state: str = "successful",
    country: str = "MX",
    category_slug: str = "games/video games",
) -> ProjectRecord:
    return ProjectRecord(
        project_id=pid,
        name=f"p{pid}",
        creator_name=creator,
        creator_slug=creator.lower().replace(" ", "-"),
        state=state,
        category_name="Video Games",
        category_slug=category_slug,
        location_country=country,
        location_display="CDMX, Mexico",
        pledged_original=usd,
        currency="USD",
        usd_pledged=usd,
        project_url=f"https://example.com/{pid}",
    )


def test_filter_scope_only_successful_videogames_mx() -> None:
    data = [
        _record(1, "Studio A", 1000),
        _record(2, "Studio B", 800, country="US"),
        _record(3, "Studio C", 700, category_slug="games/tabletop games"),
        _record(4, "Studio D", 600, state="failed"),
    ]
    result = filter_target_scope(data)
    assert len(result) == 1
    assert result[0].project_id == 1


def test_top_projects_sorted_by_usd() -> None:
    data = [
        _record(1, "A", 100),
        _record(2, "B", 900),
        _record(3, "C", 500),
    ]
    rows = TopProjectsMX().compute(data, StatsContext(top_n=2))
    assert [r["name"] for r in rows] == ["p2", "p3"]


def test_top_creators_aggregates_multiple_projects() -> None:
    data = [
        _record(1, "A Studio", 100),
        _record(2, "A Studio", 250),
        _record(3, "B Studio", 300),
    ]
    rows = TopCreatorsMX().compute(data, StatsContext(top_n=5))
    assert rows[0]["creator"] == "A Studio"
    assert rows[0]["projects"] == 2
    assert rows[0]["usd_total"] == 350

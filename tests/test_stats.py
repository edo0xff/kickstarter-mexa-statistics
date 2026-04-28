from ks_stats.models import ProjectRecord
from ks_stats.stats import TopCreatorsMX, TopProjectsMX, StatsContext, filter_target_scope


def _record(
    pid: int,
    creator: str,
    usd: float,
    state: str = "successful",
    country: str = "MX",
    category_slug: str = "games/video games",
    launched_at_iso: str | None = None,
    launched_at_epoch: int | None = None,
    deadline_iso: str | None = None,
    deadline_epoch: int | None = None,
    updated_at_iso: str | None = None,
    updated_at_epoch: int | None = None,
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
        launched_at_iso=launched_at_iso,
        launched_at_epoch=launched_at_epoch,
        deadline_iso=deadline_iso,
        deadline_epoch=deadline_epoch,
        updated_at_iso=updated_at_iso,
        updated_at_epoch=updated_at_epoch,
        project_image_url=f"https://img.example.com/{pid}.jpg",
        creator_photo_url=f"https://avatar.example.com/{creator.lower().replace(' ', '-')}.jpg",
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


def test_top_projects_sorted_by_mxn_converted_from_original_currency() -> None:
    data = [
        _record(1, "A", 100),
        _record(2, "B", 600),
        _record(3, "C", 500),
    ]
    data[0].currency = "MXN"
    data[0].pledged_original = 12000
    data[1].currency = "USD"
    data[1].pledged_original = 600
    data[2].currency = "USD"
    data[2].pledged_original = 500

    rows = TopProjectsMX().compute(data, StatsContext(top_n=2, rates={"MXN": 20.0, "USD": 1.0}))
    assert [r["name"] for r in rows] == ["p1", "p2"]
    assert rows[0]["mxn"] == 12000
    assert rows[1]["mxn"] == 12000
    assert rows[0]["project_image_url"] == "https://img.example.com/1.jpg"


def test_top_projects_includes_date_fields() -> None:
    data = [
        _record(
            1,
            "A",
            100,
            launched_at_iso="2023-01-10T00:00:00Z",
            launched_at_epoch=1673308800,
            deadline_iso="2023-02-10T00:00:00Z",
            deadline_epoch=1675987200,
            updated_at_iso="2023-02-05T12:30:00Z",
            updated_at_epoch=1675600200,
        )
    ]
    rows = TopProjectsMX().compute(data, StatsContext(top_n=1, rates={"MXN": 20.0, "USD": 1.0}))
    assert rows[0]["launched_at_iso"] == "2023-01-10T00:00:00Z"
    assert rows[0]["launched_at_epoch"] == 1673308800
    assert rows[0]["deadline_iso"] == "2023-02-10T00:00:00Z"
    assert rows[0]["deadline_epoch"] == 1675987200
    assert rows[0]["updated_at_iso"] == "2023-02-05T12:30:00Z"
    assert rows[0]["updated_at_epoch"] == 1675600200


def test_top_creators_aggregates_multiple_projects() -> None:
    data = [
        _record(1, "A Studio", 100),
        _record(2, "A Studio", 250),
        _record(3, "B Studio", 300),
    ]
    rows = TopCreatorsMX().compute(data, StatsContext(top_n=5, rates={"MXN": 20.0, "USD": 1.0}))
    assert rows[0]["creator"] == "A Studio"
    assert rows[0]["projects"] == 2
    assert rows[0]["usd_total"] == 350
    assert rows[0]["mxn_total"] == 7000
    assert rows[0]["creator_url"] == "https://www.kickstarter.com/profile/a-studio"
    assert rows[0]["creator_photo_url"] == "https://avatar.example.com/a-studio.jpg"


def test_top_creators_sorted_by_mxn_total_with_currency_conversion() -> None:
    data = [
        _record(1, "A Studio", 200),
        _record(2, "A Studio", 200),
        _record(3, "B Studio", 300),
    ]
    data[0].currency = "MXN"
    data[0].pledged_original = 7000
    data[1].currency = "MXN"
    data[1].pledged_original = 7000
    data[2].currency = "USD"
    data[2].pledged_original = 650

    rows = TopCreatorsMX().compute(data, StatsContext(top_n=5, rates={"MXN": 20.0, "USD": 1.0}))
    assert rows[0]["creator"] == "A Studio"
    assert rows[0]["mxn_total"] == 14000


def test_from_discover_project_parses_epoch_date_fields() -> None:
    record = ProjectRecord.from_discover_project(
        {
            "id": 99,
            "name": "Project",
            "creator": {"name": "Creator", "slug": "creator"},
            "state": "successful",
            "category": {"name": "Video Games", "slug": "games/video games"},
            "location": {"country": "MX", "displayable_name": "CDMX, Mexico"},
            "pledged": 10,
            "currency": "USD",
            "usd_pledged": 10,
            "urls": {"web": {"project": "https://example.com/p"}},
            "launched_at": 1673308800,
            "deadline": 1675987200,
            "updated_at": 1675600200,
        }
    )
    assert record.launched_at_iso == "2023-01-10T00:00:00Z"
    assert record.launched_at_epoch == 1673308800
    assert record.deadline_iso == "2023-02-10T00:00:00Z"
    assert record.deadline_epoch == 1675987200
    assert record.updated_at_iso == "2023-02-05T12:30:00Z"
    assert record.updated_at_epoch == 1675600200


def test_from_discover_project_parses_iso_and_missing_date_fields() -> None:
    record = ProjectRecord.from_discover_project(
        {
            "id": 100,
            "name": "Project",
            "creator": {"name": "Creator", "slug": "creator"},
            "state": "successful",
            "category": {"name": "Video Games", "slug": "games/video games"},
            "location": {"country": "MX", "displayable_name": "CDMX, Mexico"},
            "pledged": 10,
            "currency": "USD",
            "usd_pledged": 10,
            "urls": {"web": {"project": "https://example.com/p"}},
            "launched_at": "2023-03-01T13:45:00Z",
            "deadline": None,
            "updated_at": "",
        }
    )
    assert record.launched_at_iso == "2023-03-01T13:45:00Z"
    assert record.launched_at_epoch == 1677678300
    assert record.deadline_iso is None
    assert record.deadline_epoch is None
    assert record.updated_at_iso is None
    assert record.updated_at_epoch is None

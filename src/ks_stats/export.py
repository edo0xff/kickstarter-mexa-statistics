from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml


def build_export_payload(
    *,
    country_code: str,
    top_n: int,
    total_records: int,
    scoped_records: int,
    rates: dict[str, float],
    top_projects: list[dict[str, Any]],
    top_creators: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "country_code": country_code.upper(),
            "category": "Video Games",
            "project_state": "successful",
        },
        "summary": {
            "total_records": total_records,
            "scoped_records": scoped_records,
            "top_n": top_n,
        },
        "fx": {
            "base": "USD",
            "rates": rates,
        },
        "rankings": {
            "top_projects": top_projects,
            "top_creators": top_creators,
        },
    }


def write_export_file(payload: dict[str, Any], *, output_format: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return

    if output_format == "yaml":
        output_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return

    raise ValueError(f"Unsupported output format: {output_format}")
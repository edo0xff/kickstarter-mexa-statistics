from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .export import build_export_payload, write_export_file
from .fx import FxProvider
from .output import print_chart, print_summary, print_top_creators, print_top_projects
from .scraper import ScrapeBlockedError, ScrapeConfig, KickstarterDiscoverScraper
from .stats import compute_all, filter_target_scope

app = typer.Typer(add_completion=False, help="CLI no interactiva para estadisticas de Kickstarter.")


@app.callback()
def root() -> None:
    """Root command group for ks-stats."""


@app.command()
def run(
    top_n: int = typer.Option(20, min=1, help="Top N para los dos rankings."),
    country_code: str = typer.Option("MX", help="Codigo de pais del creador (ISO-2), ej. MX."),
    max_pages: int = typer.Option(6, min=1, help="Paginas Discover a consultar."),
    max_projects: int = typer.Option(400, min=1, help="Maximo de proyectos a procesar."),
    delay_ms: int = typer.Option(700, min=0, help="Delay entre requests para scraping responsable."),
    timeout_s: int = typer.Option(20, min=5, help="Timeout HTTP en segundos."),
    cache_ttl_min: int = typer.Option(120, min=1, help="TTL de cache de Discover (minutos)."),
    show_chart: bool = typer.Option(True, "--show-chart/--no-show-chart", help="Mostrar graficas ASCII en CLI."),
    output_format: str = typer.Option("table", help="Formato de salida: table, yaml o json."),
    output_file: Path | None = typer.Option(None, help="Archivo destino para salida yaml/json."),
) -> None:
    console = Console()

    normalized_output_format = output_format.strip().lower()
    if normalized_output_format not in {"table", "yaml", "json"}:
        raise typer.BadParameter("--output-format debe ser: table, yaml o json")

    if normalized_output_format == "table" and output_file is not None:
        raise typer.BadParameter("--output-file solo aplica cuando --output-format es yaml o json")

    scraper = KickstarterDiscoverScraper(
        cache_file=Path(".cache/discover_cache.json"),
        config=ScrapeConfig(
            max_pages=max_pages,
            max_projects=max_projects,
            country_code=country_code,
            delay_ms=delay_ms,
            timeout_s=timeout_s,
            cache_ttl_minutes=cache_ttl_min,
        ),
    )

    try:
        records = scraper.collect()
    except ScrapeBlockedError as exc:
        console.print(f"[bold red]Bloqueo anti-bot detectado:[/bold red] {exc}")
        raise typer.Exit(code=2)

    scoped = filter_target_scope(records, country_code=country_code)

    fx = FxProvider(cache_file=Path(".cache/fx_rates.json"))
    rates = fx.get_rates()
    mxn_per_usd = float(rates.get("MXN", 0.0))

    results = compute_all(records, top_n=top_n, country_code=country_code)
    top_projects = results.get("top_projects_mx", [])
    top_creators = results.get("top_creators_mx", [])

    if normalized_output_format == "table":
        print_summary(console, total_records=len(records), scoped_records=len(scoped))
        print_top_projects(console, top_projects, rates_mxn_per_usd=mxn_per_usd)
        print_top_creators(console, top_creators, rates_mxn_per_usd=mxn_per_usd)

        if show_chart:
            labels = [str(row["name"])[:20] for row in top_projects[: min(top_n, 15)]]
            values = [float(row["usd"]) for row in top_projects[: min(top_n, 15)]]
            print_chart(console, "Top proyectos (USD)", labels, values)
        return

    export_payload = build_export_payload(
        country_code=country_code,
        top_n=top_n,
        total_records=len(records),
        scoped_records=len(scoped),
        rates={str(k): float(v) for k, v in rates.items()},
        top_projects=top_projects,
        top_creators=top_creators,
    )

    suffix = ".yaml" if normalized_output_format == "yaml" else ".json"
    target_file = output_file or Path("artifacts") / f"ks_stats_{country_code.lower()}{suffix}"
    write_export_file(export_payload, output_format=normalized_output_format, output_path=target_file)

    console.print(
        f"[bold green]Archivo generado:[/bold green] {target_file} ({normalized_output_format.upper()})"
    )
    console.print(f"Registros incluidos: total={len(records)} | scope={len(scoped)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

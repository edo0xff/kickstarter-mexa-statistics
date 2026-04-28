from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

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
) -> None:
    console = Console()

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

    print_summary(console, total_records=len(records), scoped_records=len(scoped))
    print_top_projects(console, results.get("top_projects_mx", []), rates_mxn_per_usd=mxn_per_usd)
    print_top_creators(console, results.get("top_creators_mx", []), rates_mxn_per_usd=mxn_per_usd)

    if show_chart:
        projects = results.get("top_projects_mx", [])
        labels = [str(row["name"])[:20] for row in projects[: min(top_n, 15)]]
        values = [float(row["usd"]) for row in projects[: min(top_n, 15)]]
        print_chart(console, "Top proyectos (USD)", labels, values)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

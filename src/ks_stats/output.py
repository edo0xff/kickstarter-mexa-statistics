from __future__ import annotations

import re
from typing import Any

import plotext as plt
from rich.console import Console
from rich.table import Table


_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_BROKEN_ANSI_RE = re.compile(r"\[[0-9;]*m")


def _sanitize_plotext_output(raw: str) -> str:
    """Remove ANSI styling sequences that sometimes leak as plain text in PowerShell."""
    cleaned = _ANSI_ESCAPE_RE.sub("", raw)
    return _BROKEN_ANSI_RE.sub("", cleaned)


def print_summary(console: Console, total_records: int, scoped_records: int) -> None:
    console.print(f"[bold cyan]Registros totales obtenidos:[/bold cyan] {total_records}")
    console.print(
        f"[bold green]Registros tras filtros (successful + Video Games + MX):[/bold green] {scoped_records}"
    )


def print_top_projects(console: Console, rows: list[dict[str, Any]], rates_mxn_per_usd: float) -> None:
    table = Table(title=f"Top {len(rows)} Proyectos Video Games (MX)")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Proyecto", overflow="fold")
    table.add_column("Creador")
    table.add_column("Locacion")
    table.add_column("Moneda")
    table.add_column("Original", justify="right")
    table.add_column("USD", justify="right", style="green")
    table.add_column("MXN", justify="right", style="yellow")

    for idx, row in enumerate(rows, start=1):
        usd = float(row["usd"])
        mxn = usd * rates_mxn_per_usd
        table.add_row(
            str(idx),
            str(row["name"]),
            str(row["creator"]),
            str(row["location"]),
            str(row["currency"]),
            f"{float(row['pledged_original']):,.2f}",
            f"{usd:,.2f}",
            f"{mxn:,.2f}",
        )

    console.print(table)


def print_top_creators(console: Console, rows: list[dict[str, Any]], rates_mxn_per_usd: float) -> None:
    table = Table(title=f"Top {len(rows)} Creador/Estudio (MX) por recaudacion acumulada")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Creador")
    table.add_column("#Proyectos", justify="right")
    table.add_column("USD", justify="right", style="green")
    table.add_column("MXN", justify="right", style="yellow")

    for idx, row in enumerate(rows, start=1):
        usd = float(row["usd_total"])
        mxn = usd * rates_mxn_per_usd
        table.add_row(
            str(idx),
            str(row["creator"]),
            str(row["projects"]),
            f"{usd:,.2f}",
            f"{mxn:,.2f}",
        )

    console.print(table)


def print_chart(console: Console, title: str, labels: list[str], values: list[float]) -> None:
    if not labels:
        return

    plt.clear_data()
    plt.clear_figure()
    plt.title(title)
    plt.bar(labels, values)
    plt.plotsize(120, 20)
    plt.theme("pro")

    console.print("\n[bold magenta]Grafica:[/bold magenta]")
    chart = _sanitize_plotext_output(plt.build())
    console.print(chart, markup=False, highlight=False)

# Kickstarter Mexa Statistics

Herramienta para estadisticas de Kickstarter enfocadas en:

- Top N proyectos de Video Games en Mexico con mayor recaudacion.
- Top N creadores/estudios en Mexico con mayor recaudacion acumulada.
- Solo proyectos `successful`.

## Requisitos

- Python 3.11+

## Instalacion

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

## Uso

```powershell
.\.venv\Scripts\ks-stats.exe run
```

Ejemplo con mas control:

```powershell
.\.venv\Scripts\ks-stats.exe run --top-n 20 --max-pages 6 --max-projects 400 --delay-ms 700
```

Opciones utiles:

- `--top-n`: cantidad N para ambos rankings (default 20).
- `--country-code`: pais del creador en ISO-2 (default `MX`).
- `--max-pages`: paginas Discover a consultar.
- `--max-projects`: maximo de proyectos a procesar.
- `--delay-ms`: pausa entre requests para scraping responsable.
- `--cache-ttl-min`: minutos de vigencia del cache local.
- `--show-chart/--no-show-chart`: habilita o deshabilita graficas.

## Nota tecnica importante

Kickstarter puede aplicar protecciones anti-bot. Este proyecto:

- Ajusta el ritmo de scraping (`--delay-ms`).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

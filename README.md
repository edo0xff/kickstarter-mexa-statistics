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

Exportar a archivo YAML (ideal para integraciones):

```powershell
.\.venv\Scripts\ks-stats.exe run --output-format yaml --output-file .\artifacts\ks_stats.yaml
```

Exportar a JSON:

```powershell
.\.venv\Scripts\ks-stats.exe run --output-format json --output-file .\artifacts\ks_stats.json
```

Campos de fecha exportados por proyecto (en `rankings.top_projects`):

- `launched_at_iso` y `launched_at_epoch`: inicio de campana.
- `deadline_iso` y `deadline_epoch`: fecha final.
- `updated_at_iso` y `updated_at_epoch`: ultima actualizacion.

Si Kickstarter no envia algun valor para un proyecto, se exporta como `null`.

Opciones utiles:

- `--top-n`: cantidad N para ambos rankings (default 20).
- `--country-code`: pais del creador en ISO-2 (default `MX`).
- `--max-pages`: paginas Discover a consultar.
- `--max-projects`: maximo de proyectos a procesar.
- `--delay-ms`: pausa entre requests para scraping responsable.
- `--cache-ttl-min`: minutos de vigencia del cache local.
- `--show-chart/--no-show-chart`: habilita o deshabilita graficas.
- `--output-format`: `table` (default), `yaml` o `json`.
- `--output-file`: ruta de archivo para `yaml/json` (si no se indica, se genera en `artifacts/`).

## Integracion con Astro (ejemplo)

Genera un archivo estructurado y consumelo como data source:

```powershell
.\.venv\Scripts\ks-stats.exe run --output-format yaml --output-file .\src\data\ks_stats.yaml
```

Luego en Astro puedes leer ese archivo durante build para renderizar tablas, cards o graficas web.

## Nota tecnica importante

Kickstarter puede aplicar protecciones anti-bot. Este proyecto:

- Ajusta el ritmo de scraping (`--delay-ms`).

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

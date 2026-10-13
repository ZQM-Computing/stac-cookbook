# STAC Patterns

Production-tested STAC patterns for geospatial data discovery.

## Who this is for

Earth observation engineers, satellite imagery analysts, and geospatial data engineers.

## What's inside

- `examples/` — Runnable scripts with sample data
- `tests/` — Validation tests for each pattern

## Patterns

| # | Pattern | Description |
|---|---------|-------------|
| 1 | Catalog creation | Build STAC catalogs with pystac |
| 2 | Item validation | Validate STAC items against spec |
| 3 | Search API | STAC API with stac-fastapi |
| 4 | Rasterio integration | Read/write raster data |
| 5 | Cloud deployment | Deploy to S3/GCS |
| 6 | Full workflow | End-to-end catalog pipeline |
| 7 | STAC + DuckDB | Analytics on STAC metadata |
| 8 | STAC + COG pipeline | Catalog + serve rasters |
| 9 | STAC validation | JSON Schema validation |
| 10 | STAC API server | FastAPI STAC server |
| 11 | Bulk operations | Bulk create/update/export |
| 12 | STAC for games | STAC for game asset management |

## Requirements

- Python 3.11+
- pystac >= 1.9
- rasterio >= 1.3
- stac-fastapi >= 0.7

## Quick start

```bash
pip install -e .
pytest
```

## License

MIT — see LICENSE file.

## Related repositories

- [ZQM Geospatial Patterns](https://github.com/ZQM-Computing/geospatial-patterns) — umbrella index of all geospatial pattern repos
- [postgis-patterns](https://github.com/ZQM-Computing/postgis-patterns) — production PostGIS patterns & best practices
- [duckdb-spatial-patterns](https://github.com/ZQM-Computing/duckdb-spatial-patterns) — DuckDB Spatial patterns for analytical geospatial SQL
- [geospatial-api-reference](https://github.com/ZQM-Computing/geospatial-api-reference) — OGC API - Features with FastAPI + PostGIS
- [qgis-resources](https://github.com/ZQM-Computing/qgis-resources) — QGIS expressions, PyQGIS, styles, and QField guides
- [proxmox-ceph-operations](https://github.com/ZQM-Computing/proxmox-ceph-operations) — Proxmox VE + Ceph operations runbooks
- [ollama-fleet-patterns](https://github.com/ZQM-Computing/ollama-fleet-patterns) — Ollama fleet operations & a minimal RAG reference

*Part of [ZQM Labs](https://github.com/ZQM-Computing) — games, gear & a little mischief.*


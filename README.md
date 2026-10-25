# STAC Cookbook

<!-- ZQM-START -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <strong>ZQM Computing — Geospatial Engineering & Scientific Computing</strong><br>
  <a href="https://github.com/ZQM-Computing">ZQM Computing</a> •
  <a href="https://github.com/ZQM-Labs">ZQM Labs</a>
</p>
<!-- markdownlint-enable MD033 -->
<!-- ZQM-END -->

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![GitHub](https://img.shields.io/github/stars/ZQM-Computing/stac-cookbook?style=social)
[![CI](https://github.com/ZQM-Computing/stac-cookbook/actions/workflows/ci.yml/badge.svg)](https://github.com/ZQM-Computing/stac-cookbook/actions/workflows/ci.yml)

A **SpatioTemporal Asset Catalog (STAC) cookbook** for geospatial data discovery and imagery metadata. Learn to create catalogs, collections, and items; validate STAC metadata; explore search APIs; and connect asset records to DuckDB analytics and Cloud Optimized GeoTIFF (COG) assets. Intended for geospatial data engineers and remote-sensing developers; examples are reproducible patterns and do not imply a live or hosted catalog.

## Repository role and status

**Status:** Active, public.

**What this repository is:** A set of standalone STAC examples for building catalogs, collections, and items; validating metadata; exploring search APIs; and integrating with DuckDB and COG workflows.

**What it contributes:** Part of the ZQM Computing geospatial portfolio. This repository provides examples and guidance for the tools and workflows described below; validate each example against your own data, software versions, and operating environment before adopting it. The umbrella index for the series is [geospatial-cookbooks](https://github.com/ZQM-Computing/geospatial-cookbooks).

**Standing:** This repository is maintained independently. Automated checks cover only the paths and environments configured in its workflows; they do not establish production readiness or operational certification.

## Who this is for

Earth observation engineers, satellite imagery analysts, and geospatial data engineers. STAC (SpatioTemporal Asset Catalog) is how modern imagery archives describe themselves; these patterns cover the full lifecycle from catalog creation to API serving.

## Prerequisites

- Python 3.11+
- `pystac >= 1.9` for catalog building; `rasterio >= 1.3` for raster examples; `stac-fastapi` for the search/server examples

```bash
pip install pystac rasterio
```

## Quickstart

```bash
# Build and validate a catalog — self-contained, synthetic data
python examples/01-catalog-creation/run.py
python examples/02-item-validation/run.py

# Serve it as a STAC API (from the example header)
uvicorn examples/10-stac-api-server/run:app --reload
```

## Usage

Each pattern is a self-contained, runnable example. Start from the
[Quickstart](#quickstart), then open any entry in the [Patterns](#patterns)
list and run it end to end. Copy the pattern into your own project and
swap in your data — the patterns are reference implementations, not a
package to install.

## Patterns

| # | Example | What it demonstrates |
|---|---------|----------------------|
| 01 | `01-catalog-creation` | Building a STAC catalog, collections, and items with pystac |
| 02 | `02-item-validation` | Validating STAC items against the spec |
| 03 | `03-search-api` | STAC search API server-side setup with stac-fastapi |
| 04 | `04-rasterio-integration` | Reading raster data behind STAC assets with rasterio |
| 05 | `05-cloud-deployment` | Publishing a catalog for S3/GCS-hosted assets |
| 06 | `06-full-workflow` | End-to-end catalog pipeline: create → validate → publish |
| 07 | `07-stac-duckdb` | Querying STAC metadata catalogs with DuckDB |
| 08 | `08-stac-cog-pipeline` | Catalog + serve: STAC items pointing at Cloud Optimized GeoTIFFs |
| 09 | `09-stac-validation` | JSON Schema validation of STAC documents |
| 10 | `10-stac-api-server` | Full STAC API server with FastAPI (`uvicorn ... --reload`) |
| 11 | `11-bulk-operations` | Bulk create, update, and export of items |
| 12 | `12-stac-games` | Cataloging non-EO assets with STAC (worked example: game assets) |

## Repository layout

```text
stac-cookbook/
├── examples/
│   ├── 01-catalog-creation/run.py
│   └── ... (one run.py per pattern, 12 total)
├── tests/
│   └── test_patterns.py     # exact inventory, syntax checks, and offline runtime tests
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## Validation

For local validation, install the configured tools and run:

```bash
python -m pip install pytest ruff
python -m ruff check examples tests
python -m ruff format --check examples tests
python -m pytest -q
```

The Python CI job runs the same Ruff checks and pytest suite for code changes. The separate documentation job checks repository metadata and documentation. Markdown-only changes are excluded from the general CI workflow; prose lint runs through its own workflow.

## Roadmap

- STAC API client patterns (`pystac-client` queries, pagination)
- Collection-level summaries and range summaries
- Webhook/event-driven catalog updates

## Contributing

See [CONTRIBUTING.md](https://github.com/ZQM-Computing/stac-cookbook/blob/main/CONTRIBUTING.md). Report security issues to <zqmcomputing@gmail.com> — please do not open a public issue for those.

## Related repositories

- [postgis-cookbook](https://github.com/ZQM-Computing/postgis-cookbook) — PostGIS SQL examples: spatial indexing, joins & KNN, SRID management, vector tiles, data quality, partitioning
- [duckdb-spatial-cookbook](https://github.com/ZQM-Computing/duckdb-spatial-cookbook) — DuckDB Spatial patterns for analytical geospatial SQL: GeoParquet, spatial joins, KNN, H3 aggregation — no server required
- [pgrouting-cookbook](https://github.com/ZQM-Computing/pgrouting-cookbook) — pgRouting network analysis on PostGIS: shortest path, driving distance, isochrones, turn restrictions, traffic-aware routing
- [geopandas-cookbook](https://github.com/ZQM-Computing/geopandas-cookbook) — GeoPandas/Shapely patterns for Python geospatial workflows: spatial joins, CRS handling, overlays, interpolation, performance
- [gdal-cookbook](https://github.com/ZQM-Computing/gdal-cookbook) — GDAL/OGR command-line examples for conversion, reprojection, clipping, and mosaicking
- [maplibre-cookbook](https://github.com/ZQM-Computing/maplibre-cookbook) — MapLibre GL JS patterns for frontend vector tile rendering: custom layers, 3D terrain, performance tuning, interactive maps
- [cog-cookbook](https://github.com/ZQM-Computing/cog-cookbook) — Cloud Optimized GeoTIFF patterns: creation, validation, TiTiler serving, xarray integration, performance benchmarking
- [geoparquet-cookbook](https://github.com/ZQM-Computing/geoparquet-cookbook) — GeoParquet patterns for columnar geospatial analytics: partitioning, predicate pushdown, DuckDB/Spark integration
- [h3-cookbook](https://github.com/ZQM-Computing/h3-cookbook) — H3 hexagonal grid patterns: indexing, aggregation, visualization, grid comparisons, performance benchmarks
- [qgis-resources](https://github.com/ZQM-Computing/qgis-resources) — QGIS expressions, PyQGIS snippets, Processing scripts, styles, and QField field-collection guides
- [geospatial-api-reference](https://github.com/ZQM-Computing/geospatial-api-reference) — OGC API – Features reference implementation with FastAPI and PostGIS backends
- [ollama-fleet-cookbook](https://github.com/ZQM-Computing/ollama-fleet-cookbook) — Ollama fleet operations: model management, health checks, load-spreading, VRAM budgeting, dependency-light RAG
- [proxmox-ceph-operations](https://github.com/ZQM-Computing/proxmox-ceph-operations) — Proxmox VE + Ceph operations runbooks: health checks, backup discipline, OSD replacement, upgrade checklists
- [geospatial-cookbooks](https://github.com/ZQM-Computing/geospatial-cookbooks) — Umbrella index for ZQM Computing geospatial cookbooks

## Documentation and validation

For setup instructions, reproducible examples, data provenance, CRS/SRID assumptions, security guidance, and dependency labels, follow the [ZQM geospatial repository documentation standard](https://github.com/ZQM-Computing/geospatial-cookbooks/blob/main/docs/repository-documentation-standard.md).

The configured CI workflow is the source of truth for automated checks. A passing workflow establishes only that its checks passed for that commit; it does not certify production deployment or prove that every dependency and operating environment was covered.

## Installation

No package installation — clone the repository; the examples are standalone scripts (pyproject.toml carries metadata and tool configuration only, there is no installable package). Install just the dependencies for the pattern you are running — see Prerequisites above.

## License

MIT — see LICENSE file.

*Part of [ZQM Computing](https://github.com/ZQM-Computing) — geospatial engineering, scientific computing, and infrastructure patterns; the geospatial arm of [ZQM Labs](https://zqmlabs.com), makers of Z's Quests & Mischief location games.*

<!-- ZQM-FOOTER-START -->
<!-- markdownlint-disable MD033 -->
---

<p align="center">
  <em>Play more. Plan less.</em><br>
  <a href="https://zqmlabs.com">zqmlabs.com</a> •
  <a href="https://github.com/ZQM-Labs">ZQM Labs</a> •
  <a href="https://github.com/ZQM-Computing">ZQM Computing</a>
</p>
<!-- markdownlint-enable MD033 -->
<!-- ZQM-FOOTER-END -->

#!/usr/bin/env python3
"""Example 07: Query STAC metadata with DuckDB."""
import duckdb
import json
from pathlib import Path

# Create synthetic STAC catalog
catalog = {
    "type": "Catalog",
    "id": "zqm-demo",
    "description": "Demo STAC catalog",
    "stac_version": "1.0.0",
    "links": []
}

items = []
for i in range(10):
    item = {
        "type": "Feature",
        "id": f"item-{i}",
        "stac_version": "1.0.0",
        "geometry": {"type": "Point", "coordinates": [-80.93 + i*0.01, 29.02 + i*0.01]},
        "bbox": [-80.93 + i*0.01, 29.02 + i*0.01, -80.93 + i*0.01, 29.02 + i*0.01],
        "properties": {
            "datetime": f"2026-01-{15+i:02d}T00:00:00Z",
            "platform": "demo-satellite",
            "cloud_cover": i * 5,
            "gsd": 10 + i
        },
        "assets": {
            "data": {"href": f"https://example.com/data/{i}.tif"}
        },
        "links": []
    }
    items.append(item)

# Save as JSON
Path("output/stac_items.json").write_text(json.dumps(items))

# Query with DuckDB
con = duckdb.connect()
con.execute("INSTALL json; LOAD json;")

result = con.execute("""
    SELECT
        id,
        properties.cloud_cover,
        properties.gsd,
        properties.platform,
        ST_AsText(ST_Point(
            geometry.coordinates[1],
            geometry.coordinates[2]
        )) as wkt
    FROM 'output/stac_items.json'
    WHERE properties.cloud_cover < 30
    ORDER BY properties.cloud_cover
""").fetchdf()

print("=== STAC items with cloud_cover < 30 ===")
print(result)

# Aggregate stats
stats = con.execute("""
    SELECT
        COUNT(*) as total_items,
        AVG(properties.cloud_cover) as avg_cloud_cover,
        MIN(properties.gsd) as min_gsd,
        MAX(properties.gsd) as max_gsd
    FROM 'output/stac_items.json'
""").fetchdf()

print("\n=== Catalog statistics ===")
print(stats)

con.close()

#!/usr/bin/env python3
"""Example 08: STAC + COG pipeline (catalog + serve rasters)."""
from pystac import Catalog, Collection, Item, Extent, SpatialExtent, TemporalExtent
from datetime import datetime
import rasterio
from rasterio.transform import from_bounds
import numpy as np

# Step 1: Create synthetic COG
print("=== Step 1: Create synthetic COG ===")
width, height = 256, 256
data = np.random.randint(0, 255, (1, height, width), dtype=np.uint8)
west, south, east, north = -80.93, 29.02, -80.92, 29.03
transform = from_bounds(west, south, east, north, width, height)

with rasterio.open(
    "output/demo_cog.tif", "w",
    driver="GTiff", height=height, width=width, count=1,
    dtype=data.dtype, crs="EPSG:4326", transform=transform,
    tiled=True, blockxsize=256, blockysize=256,
    compress="DEFLATE"
) as dst:
    dst.write(data)
print("  Created output/demo_cog.tif")

# Step 2: Create STAC item for the COG
print("\n=== Step 2: Create STAC item ===")
item = Item(
    id="demo-cog-item",
    geometry={"type": "Polygon", "coordinates": [[
        [west, south], [east, south], [east, north], [west, north], [west, south]
    ]]},
    bbox=[west, south, east, north],
    datetime=datetime(2026, 1, 15),
    properties={
        "platform": "demo-satellite",
        "gsd": 10,
        "cloud_cover": 5,
        "proj:epsg": 4326
    }
)
item.add_asset("data", "https://example.com/demo_cog.tif", media_type="image/tiff")
print(f"  Created item: {item.id}")

# Step 3: Create collection and catalog
print("\n=== Step 3: Create collection and catalog ===")
extent = Extent(
    spatial=SpatialExtent(bboxes=[[west, south, east, north]]),
    temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1), None]])
)
collection = Collection(
    id="demo-cog-collection",
    description="Demo COG collection",
    extent=extent
)
collection.add_item(item)

catalog = Catalog(id="zqm-cog-catalog", description="ZQM COG catalog")
catalog.add_child(collection)

catalog.normalize_and_save("output/stac_catalog")
print(f"  Catalog saved: {catalog.id}")

# Step 4: Serve with TiTiler
print("\n=== Step 4: Serve with TiTiler ===")
print("  docker run -p 8080:8080 -v $(pwd)/output:/data developmentseed/titiler:latest")
print("  http://localhost:8080/cog/info?url=/data/demo_cog.tif")
print("  http://localhost:8080/cog/tiles/{z}/{x}/{y}?url=/data/demo_cog.tif")

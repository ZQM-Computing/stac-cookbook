"""Example 04: Read raster data with rasterio for STAC items."""

import numpy as np
import rasterio
from rasterio.transform import from_bounds

# Create a synthetic raster (10x10 pixels)
width, height = 10, 10
data = np.random.randint(0, 255, (1, height, width), dtype=np.uint8)

# Define georeferencing (WGS84 bounding box)
west, south, east, north = -80.93, 29.02, -80.92, 29.03
transform = from_bounds(west, south, east, north, width, height)

# Write to GeoTIFF
with rasterio.open(
    "output/demo_raster.tif",
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype=data.dtype,
    crs="EPSG:4326",
    transform=transform,
) as dst:
    dst.write(data)

# Read back
with rasterio.open("output/demo_raster.tif") as src:
    print(f"CRS: {src.crs}")
    print(f"Bounds: {src.bounds}")
    print(f"Shape: {src.shape}")
    print(f"Data min/max: {src.read(1).min()}/{src.read(1).max()}")

"""Example 08: build a real local COG and a self-contained STAC catalog."""

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import rasterio
from pystac import Catalog, Collection, Extent, Item, SpatialExtent, TemporalExtent
from rasterio.shutil import copy as raster_copy
from rasterio.transform import from_bounds

OUTPUT_DIR = Path("output")
CATALOG_DIR = OUTPUT_DIR / "stac_catalog"
COG_PATH = OUTPUT_DIR / "demo_cog.tif"
SOURCE_PATH = OUTPUT_DIR / ".demo_cog_source.tif"


def main() -> None:
    """Create a deterministic COG, catalog it, and print local serving instructions."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Create deterministic source pixels and convert them using GDAL's COG driver.
    print("=== Step 1: Create Cloud Optimized GeoTIFF ===")
    width, height = 256, 256
    data = (np.arange(width * height, dtype=np.uint32).reshape(height, width) % 251).astype(np.uint8)
    west, south, east, north = -80.93, 29.02, -80.92, 29.03
    transform = from_bounds(west, south, east, north, width, height)

    try:
        with rasterio.open(
            SOURCE_PATH,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype=data.dtype,
            crs="EPSG:4326",
            transform=transform,
            tiled=True,
            blockxsize=256,
            blockysize=256,
            compress="DEFLATE",
        ) as source:
            source.write(data, 1)

        # COG is a CreateCopy driver; a tiled GTiff alone is not proof of COG layout.
        raster_copy(
            SOURCE_PATH,
            COG_PATH,
            driver="COG",
            compress="DEFLATE",
            blocksize=256,
        )
    except Exception as error:
        raise SystemExit(
            "Could not create a Cloud Optimized GeoTIFF. Install a Rasterio/GDAL build "
            f"with the COG driver available: {error}"
        ) from error
    finally:
        SOURCE_PATH.unlink(missing_ok=True)

    with rasterio.open(COG_PATH) as dataset:
        layout = dataset.tags(ns="IMAGE_STRUCTURE").get("LAYOUT")
        if layout != "COG":
            raise SystemExit(f"Expected GDAL IMAGE_STRUCTURE LAYOUT=COG, got {layout!r}")
        print(f"  Created and verified {COG_PATH} (layout={layout})")

    # Step 2: Create a STAC Item whose asset points to the generated local file.
    print("\\n=== Step 2: Create STAC item ===")
    item = Item(
        id="demo-cog-item",
        geometry={
            "type": "Polygon",
            "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
        },
        bbox=[west, south, east, north],
        datetime=datetime(2026, 1, 15, tzinfo=UTC),
        properties={"platform": "demo-satellite", "gsd": 10, "cloud_cover": 5, "proj:epsg": 4326},
    )
    item.add_asset(
        "data",
        "../../demo_cog.tif",
        media_type="image/tiff; application=geotiff; profile=cloud-optimized",
        roles=["data"],
    )

    # Step 3: Keep collection temporal extent timezone-aware and save normalized links.
    print("\\n=== Step 3: Create STAC collection and catalog ===")
    extent = Extent(
        spatial=SpatialExtent(bboxes=[[west, south, east, north]]),
        temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1, tzinfo=UTC), None]]),
    )
    collection = Collection(id="demo-cog-collection", description="Demo COG collection", extent=extent)
    collection.add_item(item)

    catalog = Catalog(id="zqm-cog-catalog", description="ZQM COG catalog")
    catalog.add_child(collection)
    catalog.normalize_and_save(str(CATALOG_DIR))
    print(f"  Catalog saved: {catalog.id} at {CATALOG_DIR}")

    # Step 4: Print a local serving example. The container image is deliberately not pinned
    # here; production deployments should pin a tested TiTiler image digest.
    print("\\n=== Step 4: Serve with TiTiler (optional) ===")
    print(f"  docker run --rm -p 8080:8080 -v \"$(pwd)/output:/data\" developmentseed/titiler:latest")
    print("  http://localhost:8080/cog/info?url=/data/demo_cog.tif")
    print("  http://localhost:8080/cog/tiles/{z}/{x}/{y}?url=/data/demo_cog.tif")


if __name__ == "__main__":
    main()

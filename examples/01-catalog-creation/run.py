"""Example 01: Create a STAC catalog with pystac."""

from datetime import datetime

from pystac import Catalog, Collection, Extent, Item, SpatialExtent, TemporalExtent

# Create a catalog
catalog = Catalog(id="zqm-demo-catalog", description="ZQM Demo STAC Catalog")

# Create a collection
extent = Extent(
    spatial=SpatialExtent(bboxes=[[-80.95, 28.95, -80.90, 29.05]]),
    temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1), None]]),
)
collection = Collection(
    id="zqm-demo-collection", description="Demo collection of synthetic geospatial assets", extent=extent
)

# Create an item
item = Item(
    id="demo-item-1",
    geometry={"type": "Point", "coordinates": [-80.93, 29.02]},
    bbox=[-80.93, 29.02, -80.93, 29.02],
    datetime=datetime(2026, 1, 15),
    properties={"platform": "demo-satellite", "cloud_cover": 10},
)

# Add item to collection, collection to catalog
collection.add_item(item)
catalog.add_child(collection)

# Save catalog
catalog.normalize_and_save("output/catalog")
print(f"Catalog saved: {catalog.id}")
print(f"Collection: {collection.id}")
print(f"Item: {item.id}")

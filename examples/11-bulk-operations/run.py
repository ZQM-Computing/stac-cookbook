"""Example 11: Bulk STAC operations."""

from datetime import datetime, timedelta

from pystac import Catalog, Collection, Extent, Item, SpatialExtent, TemporalExtent

# Bulk create items
print("=== Bulk item creation ===")
items = []
base_date = datetime(2026, 1, 1)

for i in range(100):
    item = Item(
        id=f"bulk-item-{i:04d}",
        geometry={"type": "Point", "coordinates": [-80.93 + (i % 10) * 0.01, 29.02 + (i // 10) * 0.01]},
        bbox=[-80.93 + (i % 10) * 0.01, 29.02 + (i // 10) * 0.01, -80.93 + (i % 10) * 0.01, 29.02 + (i // 10) * 0.01],
        datetime=base_date + timedelta(days=i),
        properties={"index": i, "cloud_cover": (i * 7) % 100, "platform": "demo-satellite"},
    )
    items.append(item)

print(f"  Created {len(items)} items")

# Bulk add to collection
extent = Extent(
    spatial=SpatialExtent(bboxes=[[-80.95, 28.95, -80.83, 29.12]]),
    temporal=TemporalExtent(intervals=[[base_date, None]]),
)
collection = Collection(id="bulk-collection", description="Bulk demo", extent=extent)

for item in items:
    collection.add_item(item)

print(f"  Added to collection: {collection.id}")

# Bulk query
print("\n=== Bulk queries ===")

# Filter by cloud cover
low_cloud = [i for i in items if i.properties["cloud_cover"] < 20]
print(f"  Items with cloud_cover < 20: {len(low_cloud)}")

# Filter by date range
jan_items = [i for i in items if i.datetime.month == 1]
print(f"  Items in January: {len(jan_items)}")

# Group by platform
from collections import defaultdict

by_platform = defaultdict(list)
for item in items:
    by_platform[item.properties["platform"]].append(item)
print(f"  Platforms: {list(by_platform.keys())}")

# Bulk update
print("\n=== Bulk update ===")
for item in items:
    item.properties["processed"] = True
print(f"  Updated {len(items)} items with 'processed' flag")

# Bulk export
print("\n=== Bulk export ===")
catalog = Catalog(id="bulk-catalog", description="Bulk demo catalog")
catalog.add_child(collection)
catalog.normalize_and_save("output/bulk_catalog")
print(f"  Catalog saved: {catalog.id}")
print(f"  Total items: {len(list(collection.get_items()))}")

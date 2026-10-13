#!/usr/bin/env python3
"""Example 06: Full STAC workflow."""
from pystac import Catalog, Collection, Item, Extent, SpatialExtent, TemporalExtent
from datetime import datetime
import json

# 1. Create catalog
catalog = Catalog(id="zqm-full-workflow", description="Full STAC workflow demo")

# 2. Create collection
extent = Extent(
    spatial=SpatialExtent(bboxes=[[-80.95, 28.95, -80.90, 29.05]]),
    temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1), None]])
)
collection = Collection(id="demo-collection", description="Demo", extent=extent)

# 3. Add items
for i in range(3):
    item = Item(
        id=f"demo-item-{i}",
        geometry={"type": "Point", "coordinates": [-80.93 + i*0.01, 29.02 + i*0.01]},
        bbox=[-80.93 + i*0.01, 29.02 + i*0.01, -80.93 + i*0.01, 29.02 + i*0.01],
        datetime=datetime(2026, 1, 15),
        properties={"index": i, "platform": "demo"}
    )
    collection.add_item(item)

catalog.add_child(collection)

# 4. Validate
for item in collection.get_items():
    item_dict = item.to_dict()
    assert "id" in item_dict
    assert "geometry" in item_dict
    print(f"Validated: {item.id}")

# 5. Save
catalog.normalize_and_save("output/full_workflow")
print(f"\nCatalog saved with {len(list(collection.get_items()))} items")
print("Output: output/full_workflow")

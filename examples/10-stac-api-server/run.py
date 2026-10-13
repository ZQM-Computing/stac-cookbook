#!/usr/bin/env python3
"""Example 10: STAC API server with FastAPI."""
# Run with: uvicorn examples/10-stac-api-server/run:app --reload

from fastapi import FastAPI, Query
from pystac import Catalog, Collection, Item, Extent, SpatialExtent, TemporalExtent
from datetime import datetime
from typing import Optional, List

app = FastAPI(title="ZQM STAC API", version="1.0.0")

# Create in-memory catalog
catalog = Catalog(id="zqm-api", description="ZQM STAC API")

extent = Extent(
    spatial=SpatialExtent(bboxes=[[-80.95, 28.95, -80.90, 29.05]]),
    temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1), None]])
)
collection = Collection(id="demo", description="Demo collection", extent=extent)

# Add sample items
for i in range(5):
    item = Item(
        id=f"item-{i}",
        geometry={"type": "Point", "coordinates": [-80.93 + i*0.01, 29.02 + i*0.01]},
        bbox=[-80.93 + i*0.01, 29.02 + i*0.01, -80.93 + i*0.01, 29.02 + i*0.01],
        datetime=datetime(2026, 1, 15),
        properties={"index": i, "cloud_cover": i * 10}
    )
    collection.add_item(item)

catalog.add_child(collection)

# Build lookup dict for O(1) access in endpoints
items_by_id = {item.id: item for item in collection.get_items()}


@app.get("/")
def root():
    return catalog.to_dict()


@app.get("/collections")
def get_collections():
    return [c.to_dict() for c in catalog.get_collections()]


@app.get("/collections/{collection_id}")
def get_collection(collection_id: str):
    col = catalog.get_child(collection_id)
    return col.to_dict() if col else {"error": "Not found"}


@app.get("/collections/{collection_id}/items")
def get_items(collection_id: str, limit: int = 10):
    col = catalog.get_child(collection_id)
    if not col:
        return {"error": "Not found"}
    items = [items_by_id[item_id] for item_id in list(items_by_id.keys())[:limit]]
    return {
        "type": "FeatureCollection",
        "features": [i.to_dict() for i in items]
    }


@app.get("/search")
def search(
    bbox: Optional[str] = Query(None, description="Bounding box: minx,miny,maxx,maxy"),
    datetime: Optional[str] = Query(None, description="Datetime range"),
    limit: int = 10
):
    """Simple STAC search endpoint."""
    items = [items_by_id[item_id] for item_id in list(items_by_id.keys())]
    
    if bbox:
        minx, miny, maxx, maxy = [float(x) for x in bbox.split(",")]
        filtered = []
        for item in items:
            item_bbox = item.bbox
            if (item_bbox[0] <= maxx and item_bbox[2] >= minx and
                item_bbox[1] <= maxy and item_bbox[3] >= miny):
                filtered.append(item)
        items = filtered
    
    return {
        "type": "FeatureCollection",
        "features": [i.to_dict() for i in items[:limit]]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

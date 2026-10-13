#!/usr/bin/env python3
"""Example 12: STAC for game asset management (ZQM Labs angle)."""
from pystac import Catalog, Collection, Item, Extent, SpatialExtent, TemporalExtent
from datetime import datetime
import json

# Create a STAC catalog for game assets
print("=== STAC for Game Asset Management ===")
print("Use case: Track game locations, assets, and content packs")
print()

# Catalog for ZQM Labs games
catalog = Catalog(
    id="zqm-labs-game-assets",
    description="ZQM Labs game asset catalog"
)

# Collection: game locations
location_extent = Extent(
    spatial=SpatialExtent(bboxes=[[-80.95, 28.95, -80.90, 29.05]]),
    temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1), None]])
)
locations = Collection(
    id="game-locations",
    description="Game locations and checkpoints",
    extent=location_extent
)

# Add game locations as STAC items
game_stops = [
    {"id": "stop-1", "name": "The Welcome Pumpkin", "lat": 29.0258, "lng": -80.9270, "scare": "cozy"},
    {"id": "stop-2", "name": "The Whispering Oak", "lat": 29.0262, "lng": -80.9264, "scare": "cozy"},
    {"id": "stop-3", "name": "The Giggling Graveyard", "lat": 29.0266, "lng": -80.9258, "scare": "spooky"},
    {"id": "stop-4", "name": "The Spider's Web", "lat": 29.0270, "lng": -80.9252, "scare": "spooky"},
    {"id": "stop-5", "name": "The Haunted Lighthouse", "lat": 29.0275, "lng": -80.9245, "scare": "afterdark"},
    {"id": "stop-6", "name": "The Final Lantern", "lat": 29.0280, "lng": -80.9240, "scare": "afterdark"},
]

for stop in game_stops:
    item = Item(
        id=stop["id"],
        geometry={"type": "Point", "coordinates": [stop["lng"], stop["lat"]]},
        bbox=[stop["lng"], stop["lat"], stop["lng"], stop["lat"]],
        datetime=datetime(2026, 10, 30),
        properties={
            "name": stop["name"],
            "scare_level": stop["scare"],
            "game": "wisp-lost-lanterns",
            "asset_type": "game_stop"
        }
    )
    locations.add_item(item)

catalog.add_child(locations)

# Collection: content packs
content_extent = Extent(
    spatial=SpatialExtent(bboxes=[[-80.95, 28.95, -80.90, 29.05]]),
    temporal=TemporalExtent(intervals=[[datetime(2026, 1, 1), None]])
)
content = Collection(
    id="content-packs",
    description="Game content packs and assets",
    extent=content_extent
)

# Add content pack items
content_packs = [
    {"id": "pack-cozy", "name": "Cozy Glow Pack", "scare": "cozy", "assets": 12},
    {"id": "pack-spooky", "name": "Spooky Pack", "scare": "spooky", "assets": 15},
    {"id": "pack-afterdark", "name": "After Dark Pack", "scare": "afterdark", "assets": 18},
]

for pack in content_packs:
    item = Item(
        id=pack["id"],
        geometry={"type": "Point", "coordinates": [-80.925, 29.025]},
        bbox=[-80.925, 29.025, -80.925, 29.025],
        datetime=datetime(2026, 10, 1),
        properties={
            "name": pack["name"],
            "scare_level": pack["scare"],
            "asset_count": pack["assets"],
            "game": "wisp-lost-lanterns",
            "asset_type": "content_pack"
        }
    )
    content.add_item(item)

catalog.add_child(content)

# Save catalog
catalog.normalize_and_save("output/game_catalog")
print(f"Catalog saved: {catalog.id}")
print(f"  Collections: {len(list(catalog.get_children()))}")
print(f"  Game locations: {len(list(locations.get_items()))}")
print(f"  Content packs: {len(list(content.get_items()))}")

# Query: find all spooky/afterdark locations
print("\n=== Query: spooky and afterdark locations ===")
for item in locations.get_items():
    if item.properties["scare_level"] in ["spooky", "afterdark"]:
        print(f"  {item.properties['name']} ({item.properties['scare_level']})")

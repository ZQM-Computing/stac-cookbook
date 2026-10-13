#!/usr/bin/env python3
"""Example 09: STAC validation with JSON Schema."""
import json
from pathlib import Path
from pystac import Item
from pystac.validation import validate_dict
from datetime import datetime

# Load STAC JSON Schema
# In production, download from https://github.com/radiantearth/stac-spec
# For demo, we use pystac's built-in validation

# Create a valid item
valid_item = Item(
    id="valid-item",
    geometry={"type": "Point", "coordinates": [-80.93, 29.02]},
    bbox=[-80.93, 29.02, -80.93, 29.02],
    datetime=datetime(2026, 1, 15),
    properties={"platform": "demo"}
)

# Validate
try:
    validate_dict(valid_item.to_dict(), "Item")
    print("Valid item: PASSED")
except Exception as e:
    print(f"Valid item: FAILED - {e}")

# Create an invalid item (missing required field)
invalid_dict = {
    "type": "Feature",
    "id": "invalid-item",
    "geometry": {"type": "Point", "coordinates": [-80.93, 29.02]},
    "bbox": [-80.93, 29.02, -80.93, 29.02],
    # Missing 'datetime' and 'properties'
}

try:
    validate_dict(invalid_dict, "Item")
    print("Invalid item: PASSED (unexpected)")
except Exception as e:
    print(f"Invalid item: FAILED (expected) - {type(e).__name__}")

# Custom validation rules
print("\n=== Custom validation ===")
item_dict = valid_item.to_dict()

# Check required fields
required = ["id", "geometry", "bbox", "datetime", "properties"]
for field in required:
    assert field in item_dict, f"Missing: {field}"
print("  Required fields: OK")

# Check geometry type
assert item_dict["geometry"]["type"] in ["Point", "Polygon", "MultiPolygon"]
print("  Geometry type: OK")

# Check datetime format
datetime_str = item_dict["datetime"]
assert "T" in datetime_str and "Z" in datetime_str
print("  Datetime format: OK")

# Check bbox validity
bbox = item_dict["bbox"]
assert len(bbox) == 4
assert bbox[0] < bbox[2]  # west < east
assert bbox[1] < bbox[3]  # south < north
print("  BBox validity: OK")

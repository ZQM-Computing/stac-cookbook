"""Example 02: Validate STAC items."""

from datetime import datetime

from pystac import Item
from pystac.errors import STACValidationError

# Create a valid item
item = Item(
    id="demo-item-1",
    geometry={"type": "Point", "coordinates": [-80.93, 29.02]},
    bbox=[-80.93, 29.02, -80.93, 29.02],
    datetime=datetime(2026, 1, 15),
    properties={"platform": "demo-satellite"},
)

# Validate using pystac's built-in validation
try:
    item.validate()
    print("Item is valid STAC")
except STACValidationError as e:
    print(f"Validation error: {e}")

# Check required fields
item_dict = item.to_dict()
required = ["id", "geometry", "bbox", "properties"]
for field in required:
    assert field in item_dict, f"Missing required field: {field}"
# datetime is inside properties in STAC 1.0.0
assert "datetime" in item_dict["properties"], "Missing required field: properties.datetime"
print("All required fields present")

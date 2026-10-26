"""Example 09: fail-closed STAC validation with PySTAC."""

from copy import deepcopy
from datetime import UTC, datetime

from pystac import Item, STACObjectType
from pystac.errors import STACError
from pystac.validation import validate_dict

# This example uses PySTAC's bundled validator. For production workflows,
# pin the PySTAC/STAC versions and validate against the intended extensions too.
valid_item = Item(
    id="valid-item",
    geometry={"type": "Point", "coordinates": [-80.93, 29.02]},
    # A Point can legitimately have a zero-area bbox.
    bbox=[-80.93, 29.02, -80.93, 29.02],
    datetime=datetime(2026, 1, 15, tzinfo=UTC),
    properties={"platform": "demo"},
)

try:
    validate_dict(valid_item.to_dict(), STACObjectType.ITEM)
except STACError as error:
    raise SystemExit(f"Valid item unexpectedly failed validation: {error}") from error
print("Valid item: PASSED")

invalid_dict = deepcopy(valid_item.to_dict())
# Keep the document identifiable as a STAC Item, but remove a required field
# so validation rejects it for the intended schema violation.
del invalid_dict["properties"]["datetime"]

try:
    validate_dict(invalid_dict, STACObjectType.ITEM)
except STACError as error:
    print(f"Invalid item: REJECTED as expected ({type(error).__name__})")
else:
    raise SystemExit("Invalid item unexpectedly passed validation")

print("\n=== Additional local sanity checks ===")
item_dict = valid_item.to_dict()
required = ("id", "geometry", "bbox", "properties")
missing = [field for field in required if field not in item_dict]
if missing:
    raise SystemExit(f"Valid item is missing required fields: {missing}")
if "datetime" not in item_dict["properties"]:
    raise SystemExit("Valid item is missing properties.datetime")
print("Required fields: OK")

geometry_type = item_dict["geometry"].get("type")
supported_geojson_types = {
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
}
if geometry_type not in supported_geojson_types:
    raise SystemExit(f"Unsupported GeoJSON geometry type: {geometry_type!r}")
print("Geometry type: OK")

datetime_value = item_dict["properties"]["datetime"]
if not isinstance(datetime_value, str) or "T" not in datetime_value or not datetime_value.endswith("Z"):
    raise SystemExit(f"Expected an explicit UTC timestamp, got: {datetime_value!r}")
print("Datetime format: OK")

bbox = item_dict["bbox"]
if len(bbox) not in (4, 6) or not all(isinstance(value, (int, float)) for value in bbox):
    raise SystemExit(f"Invalid bbox shape or values: {bbox!r}")
dimensions = len(bbox) // 2
if any(low > high for low, high in zip(bbox[:dimensions], bbox[dimensions:])):
    raise SystemExit(f"Reversed bbox bounds: {bbox!r}")
print("BBox validity: OK")

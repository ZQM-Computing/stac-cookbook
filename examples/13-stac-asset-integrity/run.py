"""Example 13: verify local STAC asset size and SHA-256 multihash metadata."""

from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

import pystac
from pystac import Asset, Catalog, Item

OUTPUT = Path("output/stac_asset_integrity")
FILE_EXTENSION = "https://stac-extensions.github.io/file/v2.1.0/schema.json"
ASSET_PATH = OUTPUT / "payload.bin"
CATALOG_PATH = OUTPUT / "catalog"

# Deterministic synthetic bytes make the example repeatable and network-free.
payload = b"ZQM STAC asset-integrity example\n"
OUTPUT.mkdir(parents=True, exist_ok=True)
ASSET_PATH.write_bytes(payload)

digest = sha256(payload).hexdigest()
# STAC file:checksum uses a multihash string. 0x12 = SHA-256, 0x20 = 32-byte digest.
checksum = f"1220{digest}"
item = Item(
    id="integrity-demo-item",
    geometry={"type": "Point", "coordinates": [-80.93, 29.02]},
    bbox=[-80.93, 29.02, -80.93, 29.02],
    datetime=datetime(2026, 1, 15, tzinfo=UTC),
    properties={"platform": "synthetic"},
    stac_extensions=[FILE_EXTENSION],
)
item.add_asset(
    "data",
    Asset(
        href="../../payload.bin",
        media_type="application/octet-stream",
        roles=["data"],
        extra_fields={"file:size": len(payload), "file:checksum": checksum},
    ),
)
catalog = Catalog(id="zqm-asset-integrity", description="Local asset integrity example")
catalog.add_item(item)
catalog.normalize_hrefs(str(CATALOG_PATH))
catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)

# Resolve the relative asset href from the saved Item location, then verify the
# declared size and checksum against bytes on disk. No network access is used.
saved_item = CATALOG_PATH / "integrity-demo-item" / "integrity-demo-item.json"
if not saved_item.is_file():
    raise SystemExit(f"Expected saved STAC Item was not created: {saved_item}")
saved = pystac.Item.from_file(str(saved_item))
asset = saved.assets["data"]
href = asset.href
parsed_href = urlparse(href)
if parsed_href.scheme or parsed_href.netloc or Path(href).is_absolute() or "\\" in href:
    raise SystemExit(f"Expected a relative local asset href, got: {href!r}")

asset_candidate = saved_item.parent / href
# Reject symlink components and any resolved path that escapes this example's
# output root before reading bytes. This pattern is intentionally local-only.
for component in (asset_candidate, *asset_candidate.parents):
    if component == OUTPUT.parent:
        break
    if component.is_symlink():
        raise SystemExit(f"Symlinks are not allowed in local asset paths: {component}")
try:
    asset_path = asset_candidate.resolve(strict=True)
    asset_path.relative_to(OUTPUT.resolve())
except (OSError, ValueError) as error:
    raise SystemExit(f"Local asset escapes the output root or is missing: {href}") from error
if not asset_path.is_file():
    raise SystemExit(f"Local asset does not resolve to a regular file: {href}")
actual = asset_path.read_bytes()
if asset.extra_fields.get("file:size") != len(actual):
    raise SystemExit("STAC file:size does not match local asset bytes")
if asset.extra_fields.get("file:checksum") != f"1220{sha256(actual).hexdigest()}":
    raise SystemExit("STAC file:checksum does not match local asset bytes")

print("Asset size: VERIFIED")
print("Asset SHA-256 multihash: VERIFIED")
print("Catalog saved: zqm-asset-integrity")
print("Scope: local synthetic asset only; no remote URL or production publication checked")

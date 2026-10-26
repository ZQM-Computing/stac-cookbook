"""Inventory, syntax, and offline runtime tests for the STAC cookbook."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from pystac import Asset, Catalog, Item, STACObjectType
from pystac.validation import validate_dict

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT / "examples"
EXPECTED_EXAMPLES = {
    "01-catalog-creation",
    "02-item-validation",
    "03-search-api",
    "04-rasterio-integration",
    "05-cloud-deployment",
    "06-full-workflow",
    "07-stac-duckdb",
    "08-stac-cog-pipeline",
    "09-stac-validation",
    "10-stac-api-server",
    "11-bulk-operations",
    "12-stac-games",
    "13-stac-asset-integrity",
}
OFFLINE_STAC_EXAMPLES = (
    "01-catalog-creation",
    "02-item-validation",
    "05-cloud-deployment",
    "06-full-workflow",
    "08-stac-cog-pipeline",
    "11-bulk-operations",
    "12-stac-games",
    "13-stac-asset-integrity",
)
EXPECTED_OUTPUT_MARKERS = {
    "01-catalog-creation": ("Catalog saved: zqm-demo-catalog", "Item: demo-item-1"),
    "02-item-validation": ("Item is valid STAC", "All required fields present"),
    "05-cloud-deployment": ("Catalog prepared for cloud deployment", "Catalog path: output/cloud_catalog"),
    "06-full-workflow": ("Catalog saved with 3 items", "Output: output/full_workflow"),
    "08-stac-cog-pipeline": ("Created and verified output/demo_cog.tif (layout=COG)", "Catalog saved: zqm-cog-catalog"),
    "11-bulk-operations": ("Created 100 items", "Total items: 100"),
    "12-stac-games": ("Game locations: 6", "Content packs: 3"),
    "13-stac-asset-integrity": ("Asset size: VERIFIED", "Asset SHA-256 multihash: VERIFIED"),
}
EXPECTED_CATALOGS = {
    "01-catalog-creation": ("catalog", "zqm-demo-catalog"),
    "05-cloud-deployment": ("cloud_catalog", "zqm-cloud-catalog"),
    "06-full-workflow": ("full_workflow", "zqm-full-workflow"),
    "08-stac-cog-pipeline": ("stac_catalog", "zqm-cog-catalog"),
    "11-bulk-operations": ("bulk_catalog", "bulk-catalog"),
    "12-stac-games": ("game_catalog", "zqm-labs-game-assets"),
    "13-stac-asset-integrity": ("stac_asset_integrity/catalog", "zqm-asset-integrity"),
}


def test_exact_example_inventory():
    """README's 13-example promise cannot silently regress to a partial tree."""
    scripts = sorted(EXAMPLES_DIR.glob("*/run.py"))
    actual = {path.parent.name for path in scripts}
    assert actual == EXPECTED_EXAMPLES, (
        f"Example inventory mismatch. Missing: {sorted(EXPECTED_EXAMPLES - actual)}; "
        f"unexpected: {sorted(actual - EXPECTED_EXAMPLES)}"
    )
    for script in scripts:
        assert script.stat().st_size > 0, f"Example entry point is empty: {script}"

def test_asset_integrity_example_declares_file_extension_and_confines_local_paths():
    source_path = EXAMPLES_DIR / "13-stac-asset-integrity" / "run.py"
    source = source_path.read_text(encoding="utf-8")
    assert "stac_extensions=[FILE_EXTENSION]" in source
    assert "https://stac-extensions.github.io/file/v2.1.0/schema.json" in source
    assert "parsed_href.scheme or parsed_href.netloc" in source
    assert "asset_path.relative_to(OUTPUT.resolve())" in source
    assert "Symlinks are not allowed in local asset paths" in source


def test_all_examples_have_valid_python_syntax():
    """Compile source in memory to avoid leaving __pycache__ files in the checkout."""
    scripts = sorted(EXAMPLES_DIR.glob("*/run.py"))
    assert scripts, "No examples/*/run.py scripts found"
    for script in scripts:
        compile(script.read_text(encoding="utf-8"), str(script), "exec")


def _coordinate_pairs(value):
    """Yield coordinate pairs recursively from a GeoJSON geometry coordinate tree."""
    if (
        isinstance(value, (list, tuple))
        and len(value) >= 2
        and all(isinstance(component, (int, float)) for component in value[:2])
    ):
        yield value[0], value[1]
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _coordinate_pairs(child)


def parse_stac_datetime(value: str, path: Path) -> datetime:
    """Parse an RFC 3339 timestamp and require an explicit UTC offset."""
    assert isinstance(value, str) and value, f"Invalid STAC datetime in {path}: {value!r}"
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise AssertionError(f"Invalid STAC datetime in {path}: {value!r}") from error
    assert parsed.tzinfo is not None and parsed.utcoffset() is not None, (
        f"STAC datetime must include a UTC offset in {path}: {value!r}"
    )
    return parsed


def longitude_in_bbox(longitude: float, west: float, east: float, epsilon: float = 1e-9) -> bool:
    """Test longitude membership in a normal or antimeridian-crossing interval."""
    if west <= east:
        return west - epsilon <= longitude <= east + epsilon
    return longitude >= west - epsilon or longitude <= east + epsilon


def longitude_bbox_contains(
    outer_west: float,
    outer_east: float,
    inner_west: float,
    inner_east: float,
    epsilon: float = 1e-9,
) -> bool:
    """Check whether a longitude interval is contained in another, including wrapped intervals."""
    outer_wraps = outer_west > outer_east
    inner_wraps = inner_west > inner_east
    if not outer_wraps:
        return not inner_wraps and outer_west <= inner_west + epsilon and inner_east <= outer_east + epsilon
    if inner_wraps:
        return inner_west >= outer_west - epsilon and inner_east <= outer_east + epsilon
    return inner_west >= outer_west - epsilon or inner_east <= outer_east + epsilon


def bbox_dimensions_are_valid(bbox: list, path: Path) -> None:
    """Validate bbox numeric dimensions while allowing RFC 7946 longitude wrap."""
    dimensions = len(bbox) // 2
    minima, maxima = bbox[:dimensions], bbox[dimensions:]
    for index, (low, high) in enumerate(zip(minima, maxima)):
        if index == 0 and low > high:
            continue
        assert low <= high, f"Reversed STAC bbox in {path}: {bbox}"


def assert_item_spatiotemporal_consistency(document: dict, path: Path) -> None:
    """Check STAC Item geometry, bbox, and temporal metadata agree."""
    geometry = document.get("geometry")
    bbox = document.get("bbox")
    assert isinstance(geometry, dict) and geometry.get("type"), f"Missing GeoJSON geometry in {path}"
    assert isinstance(bbox, list) and len(bbox) in (4, 6), f"Invalid STAC Item bbox in {path}: {bbox}"
    assert all(isinstance(value, (int, float)) for value in bbox), f"Non-numeric STAC Item bbox in {path}: {bbox}"
    dimensions = len(bbox) // 2
    bbox_dimensions_are_valid(bbox, path)

    coordinates = list(_coordinate_pairs(geometry.get("coordinates")))
    assert coordinates, f"Geometry has no coordinate pairs in {path}"
    for longitude, latitude in coordinates:
        assert longitude_in_bbox(longitude, bbox[0], bbox[dimensions]), (
            f"Longitude {longitude} falls outside Item bbox {bbox} in {path}"
        )
        assert bbox[1] - 1e-9 <= latitude <= bbox[dimensions + 1] + 1e-9, (
            f"Latitude {latitude} falls outside Item bbox {bbox} in {path}"
        )

    properties = document.get("properties", {})
    instant = properties.get("datetime")
    start = properties.get("start_datetime")
    end = properties.get("end_datetime")
    assert instant is not None or (start is not None and end is not None), (
        f"Item needs datetime or both start_datetime and end_datetime in {path}"
    )
    if instant is not None:
        parse_stac_datetime(instant, path)
    if start is not None:
        parse_stac_datetime(start, path)
    if end is not None:
        parse_stac_datetime(end, path)
    if start is not None and end is not None:
        assert parse_stac_datetime(start, path) <= parse_stac_datetime(end, path), (
            f"Item start_datetime is after end_datetime in {path}: {start} > {end}"
        )


def assert_collection_extent_consistency(document: dict, path: Path) -> None:
    """Check Collection spatial and temporal extent shapes and ordering."""
    extent = document.get("extent", {})
    spatial = extent.get("spatial", {}).get("bbox", [])
    temporal = extent.get("temporal", {}).get("interval", [])
    assert spatial, f"Collection has no spatial bbox extent in {path}"
    assert temporal, f"Collection has no temporal interval extent in {path}"

    for bbox in spatial:
        assert isinstance(bbox, list) and len(bbox) in (4, 6), f"Invalid Collection bbox in {path}: {bbox}"
        assert all(isinstance(value, (int, float)) for value in bbox), f"Non-numeric Collection bbox in {path}: {bbox}"
        bbox_dimensions_are_valid(bbox, path)

    for interval in temporal:
        assert isinstance(interval, list) and len(interval) == 2, (
            f"Invalid Collection temporal interval in {path}: {interval}"
        )
        start, end = interval
        parsed_start = parse_stac_datetime(start, path) if start is not None else None
        parsed_end = parse_stac_datetime(end, path) if end is not None else None
        assert parsed_start is None or parsed_end is None or parsed_start <= parsed_end, (
            f"Reversed Collection temporal interval in {path}: {interval}"
        )


def assert_local_references_resolve(catalog_path: Path) -> None:
    """Validate local STAC references stay inside the generated output root."""
    catalog_root = catalog_path.parent
    allowed_root = catalog_root.parent.resolve()
    documents = sorted(catalog_root.rglob("*.json"))
    assert documents, f"No JSON documents found under STAC output: {catalog_root}"

    for document_path in documents:
        document = json.loads(document_path.read_text(encoding="utf-8"))
        stac_type = {
            "Catalog": STACObjectType.CATALOG,
            "Collection": STACObjectType.COLLECTION,
            "Feature": STACObjectType.ITEM,
        }.get(document.get("type"))
        assert stac_type is not None, f"Unexpected STAC document type {document.get('type')!r} in {document_path}"
        validate_dict(document, stac_type)
        if stac_type == STACObjectType.ITEM:
            assert_item_spatiotemporal_consistency(document, document_path)
        elif stac_type == STACObjectType.COLLECTION:
            assert_collection_extent_consistency(document, document_path)

        for link in document.get("links", []):
            href = link.get("href")
            assert isinstance(href, str) and href, f"Empty link href in {document_path}: {link}"
            parsed = urlparse(href)
            if parsed.scheme in ("http", "https"):
                continue
            if parsed.scheme == "file":
                target = Path(unquote(parsed.path)).resolve()
            elif parsed.scheme:
                continue
            else:
                target = (document_path.parent / unquote(parsed.path)).resolve()
            assert target.is_relative_to(allowed_root), (
                f"Local STAC link escapes generated output root in {document_path}: {href}"
            )
            assert target.is_file(), f"Broken local STAC link rel={link.get('rel')!r} in {document_path}: {href}"

        for asset_key, asset in document.get("assets", {}).items():
            href = asset.get("href")
            assert isinstance(href, str) and href, f"Empty asset href for {asset_key!r} in {document_path}"
            parsed = urlparse(href)
            if parsed.scheme in ("http", "https"):
                continue
            if parsed.scheme == "file":
                target = Path(unquote(parsed.path))
            elif parsed.scheme:
                continue
            else:
                target = (document_path.parent / unquote(parsed.path)).resolve()
            assert target.is_relative_to(allowed_root), (
                f"Local STAC asset escapes generated output root in {document_path}: {href}"
            )
            assert target.is_file(), f"Broken local asset href for {asset_key!r} in {document_path}: {href}"


def assert_item_within_collection_extent(item: dict, collection: dict, path: Path) -> None:
    """Ensure an Item's spatial and temporal footprint fits its Collection extent."""
    item_bbox = item.get("bbox")
    spatial_extents = collection.get("extent", {}).get("spatial", {}).get("bbox", [])
    if isinstance(item_bbox, list) and spatial_extents:
        assert len(item_bbox) in (4, 6), f"Invalid Item bbox in {path}: {item_bbox}"

        def contains(outer: list, inner: list) -> bool:
            if len(outer) not in (4, 6) or len(inner) != len(outer):
                return False
            dimensions = len(outer) // 2
            if not longitude_bbox_contains(outer[0], outer[dimensions], inner[0], inner[dimensions]):
                return False
            if not (outer[1] <= inner[1] + 1e-9 and inner[dimensions + 1] <= outer[dimensions + 1] + 1e-9):
                return False
            if dimensions == 3:
                return outer[2] <= inner[2] + 1e-9 and inner[5] <= outer[5] + 1e-9
            return True

        assert any(contains(extent, item_bbox) for extent in spatial_extents), (
            f"Item {item.get('id')!r} bbox {item_bbox} falls outside Collection spatial extent in {path}"
        )

    def parse_datetime(value: str | None) -> datetime | None:
        return parse_stac_datetime(value, path) if value is not None else None

    properties = item.get("properties", {})
    item_start = properties.get("datetime") or properties.get("start_datetime")
    item_end = properties.get("datetime") or properties.get("end_datetime")
    temporal_extents = collection.get("extent", {}).get("temporal", {}).get("interval", [])
    if item_start is None or item_end is None or not temporal_extents:
        return

    parsed_start = parse_datetime(item_start)
    parsed_end = parse_datetime(item_end)
    assert parsed_start is not None and parsed_end is not None
    fits_interval = False
    for interval in temporal_extents:
        start, end = interval
        parsed_collection_start = parse_datetime(start)
        parsed_collection_end = parse_datetime(end)
        if (parsed_collection_start is None or parsed_collection_start <= parsed_start) and (
            parsed_collection_end is None or parsed_end <= parsed_collection_end
        ):
            fits_interval = True
            break
    assert fits_interval, (
        f"Item {item.get('id')!r} temporal range [{item_start}, {item_end}] falls outside "
        f"Collection temporal extent in {path}"
    )


def assert_item_collection_relationships(catalog_path: Path) -> None:
    """Validate local Item-to-Collection links and reverse Collection item links."""
    root = catalog_path.parent
    documents = sorted(root.rglob("*.json"))
    by_path = {path.resolve(): json.loads(path.read_text(encoding="utf-8")) for path in documents}
    collections = {
        document.get("id"): (path, document)
        for path, document in by_path.items()
        if document.get("type") == "Collection"
    }
    items = {
        document.get("id"): (path, document) for path, document in by_path.items() if document.get("type") == "Feature"
    }

    def local_target(source_path: Path, href: str) -> Path | None:
        parsed = urlparse(href)
        if parsed.scheme in ("http", "https") or (parsed.scheme and parsed.scheme != "file"):
            return None
        if parsed.scheme == "file":
            return Path(unquote(parsed.path)).resolve()
        if parsed.path.startswith("/"):
            return Path(unquote(parsed.path)).resolve()
        return (source_path.parent / unquote(parsed.path)).resolve()

    for item_id, (item_path, item) in items.items():
        collection_id = item.get("collection")
        collection_links = [link for link in item.get("links", []) if link.get("rel") == "collection"]
        if collection_id is None:
            assert not collection_links, f"Item {item_id} has a collection link but no collection ID: {item_path}"
            continue
        assert isinstance(collection_id, str) and collection_id, (
            f"Item has invalid collection ID in {item_path}: {collection_id!r}"
        )
        assert collection_links, f"Item {item_id} declares collection {collection_id!r} but has no collection link"
        for link in collection_links:
            target = local_target(item_path, link["href"])
            if target is None:
                continue
            assert target in by_path, (
                f"Item {item_id} collection link does not resolve to a local STAC document: {link['href']}"
            )
            collection = by_path[target]
            assert collection.get("type") == "Collection", (
                f"Item {item_id} collection link targets a non-Collection document: {target}"
            )
            assert collection.get("id") == collection_id, (
                f"Item {item_id} declares collection {collection_id!r}, but link targets "
                f"{collection.get('id')!r} at {target}"
            )
            assert_item_within_collection_extent(item, collection, item_path)
        if collection_id in collections:
            expected_path, _ = collections[collection_id]
            assert any(
                local_target(item_path, link["href"]) == expected_path.resolve()
                for link in collection_links
                if local_target(item_path, link["href"]) is not None
            ), f"Item {item_id} collection link does not point to the local document for collection {collection_id!r}"

    for collection_id, (collection_path, collection) in collections.items():
        for link in collection.get("links", []):
            if link.get("rel") != "item":
                continue
            target = local_target(collection_path, link["href"])
            if target is None:
                continue
            assert target in by_path, f"Collection {collection_id} item link does not resolve locally: {link['href']}"
            item = by_path[target]
            assert item.get("type") == "Feature", (
                f"Collection {collection_id} item link targets a non-Item document: {target}"
            )
            assert item.get("collection") == collection_id, (
                f"Collection {collection_id} links to Item {item.get('id')!r} whose collection "
                f"field is {item.get('collection')!r}"
            )


def assert_catalog_hierarchy(catalog_path: Path) -> None:
    """Validate local Catalog/Collection child and parent links are reciprocal."""
    documents = sorted(catalog_path.parent.rglob("*.json"))
    by_path = {path.resolve(): json.loads(path.read_text(encoding="utf-8")) for path in documents}

    def local_target(source_path: Path, href: str) -> Path | None:
        parsed = urlparse(href)
        if parsed.scheme in ("http", "https") or (parsed.scheme and parsed.scheme != "file"):
            return None
        if parsed.scheme == "file":
            return Path(unquote(parsed.path)).resolve()
        return (source_path.parent / unquote(parsed.path)).resolve()

    for source_path, source in by_path.items():
        source_type = source.get("type")
        for link in source.get("links", []):
            relation = link.get("rel")
            if relation not in ("child", "parent"):
                continue
            # Item-to-Collection parentage is validated separately; STAC Collections
            # do not require a reciprocal Catalog/Collection child link for each Item.
            if source_type == "Feature" or (relation == "child" and source_type not in ("Catalog", "Collection")):
                continue
            target_path = local_target(source_path, link["href"])
            if target_path is None:
                continue
            assert target_path in by_path, (
                f"STAC {relation} link from {source.get('id')!r} does not resolve locally: {link['href']}"
            )
            target = by_path[target_path]
            target_type = target.get("type")
            if relation == "child":
                assert source_type in ("Catalog", "Collection"), (
                    f"STAC {source_type!r} document cannot have a child link: {source_path}"
                )
                assert target_type in ("Catalog", "Collection"), (
                    f"Child link from {source.get('id')!r} targets invalid STAC type {target_type!r}"
                )
                reverse_relation = "parent"
            else:
                assert source_type in ("Collection", "Feature"), (
                    f"STAC {source_type!r} document cannot have a parent link: {source_path}"
                )
                assert target_type in ("Catalog", "Collection"), (
                    f"Parent link from {source.get('id')!r} targets invalid STAC type {target_type!r}"
                )
                reverse_relation = "child"

            reciprocal = any(
                reverse.get("rel") == reverse_relation
                and local_target(target_path, reverse.get("href", "")) == source_path
                for reverse in target.get("links", [])
                if isinstance(reverse.get("href"), str)
            )
            assert reciprocal, (
                f"Non-reciprocal STAC hierarchy link: {source_type} {source.get('id')!r} "
                f"rel={relation!r} -> {target_type} {target.get('id')!r} lacks reverse "
                f"rel={reverse_relation!r}"
            )


def test_offline_stac_examples_run_end_to_end(tmp_path):
    """Exercise deterministic examples without network access, cloud credentials, or a service."""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for name in OFFLINE_STAC_EXAMPLES:
        script = EXAMPLES_DIR / name / "run.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        assert result.returncode == 0, (
            f"{name} failed with exit code {result.returncode}.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        for marker in EXPECTED_OUTPUT_MARKERS[name]:
            assert marker in result.stdout, (
                f"{name} did not report expected result {marker!r}. stdout:\n{result.stdout}"
            )

        if name in EXPECTED_CATALOGS:
            directory, expected_id = EXPECTED_CATALOGS[name]
            catalog_path = tmp_path / "output" / directory / "catalog.json"
            assert catalog_path.is_file() and catalog_path.stat().st_size > 0, (
                f"{name} did not create a non-empty catalog: {catalog_path}"
            )
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            assert catalog.get("type") == "Catalog", f"Unexpected STAC root type in {catalog_path}"
            assert catalog.get("id") == expected_id, f"Unexpected catalog ID in {catalog_path}"
            assert catalog.get("stac_version"), f"Missing STAC version in {catalog_path}"
            assert_local_references_resolve(catalog_path)
            assert_item_collection_relationships(catalog_path)
            assert_catalog_hierarchy(catalog_path)
            if name == "08-stac-cog-pipeline":
                import rasterio

                item_path = (
                    tmp_path
                    / "output"
                    / "stac_catalog"
                    / "demo-cog-collection"
                    / "demo-cog-item"
                    / "demo-cog-item.json"
                )
                item = json.loads(item_path.read_text(encoding="utf-8"))
                asset = item["assets"]["data"]
                assert asset["href"] == "../../../demo_cog.tif"
                assert asset["type"] == "image/tiff; application=geotiff; profile=cloud-optimized"
                assert "data" in asset.get("roles", [])
                assert (item_path.parent / asset["href"]).resolve().is_file()
                assert item["properties"]["datetime"].endswith("Z")
                with rasterio.open(tmp_path / "output" / "demo_cog.tif") as dataset:
                    assert dataset.tags(ns="IMAGE_STRUCTURE").get("LAYOUT") == "COG"
                    assert dataset.width == 256 and dataset.height == 256 and dataset.count == 1


def test_stac_datetime_rejects_malformed_and_timezone_naive_values():
    """Malformed and timezone-naive timestamps must not pass as valid STAC datetimes."""
    for value in ("", "not-a-date", "2026-13-01T00:00:00Z", "2026-10-25T12:00:00"):
        try:
            parse_stac_datetime(value, Path("item.json"))
        except AssertionError:
            continue
        raise AssertionError(f"Invalid STAC datetime unexpectedly accepted: {value!r}")


def test_stac_datetime_compares_instants_across_timezone_offsets():
    """Timestamp ordering must compare instants, not their source strings."""
    earlier = parse_stac_datetime("2026-10-25T08:00:00-04:00", Path("item.json"))
    later = parse_stac_datetime("2026-10-25T13:30:00Z", Path("item.json"))
    assert earlier < later
    assert parse_stac_datetime("2026-10-25T09:00:00-04:00", Path("item.json")) == parse_stac_datetime(
        "2026-10-25T13:00:00Z", Path("item.json")
    )


def test_local_asset_reference_cannot_escape_generated_output_root(tmp_path):
    """A local file URI outside the generated output tree must fail closed."""
    output_root = tmp_path / "output"
    catalog_dir = output_root / "catalog"
    catalog_dir.mkdir(parents=True)
    outside_asset = tmp_path / "outside.bin"
    outside_asset.write_bytes(b"not part of the generated output")

    item = Item(
        id="external-local-file",
        geometry={"type": "Point", "coordinates": [-80.9, 29.0]},
        bbox=[-80.9, 29.0, -80.9, 29.0],
        datetime=datetime.fromisoformat("2026-01-15T00:00:00+00:00"),
        properties={},
    )
    item.add_asset(
        "data",
        Asset(href=outside_asset.as_uri(), media_type="application/octet-stream", roles=["data"]),
    )
    catalog = Catalog(id="root", description="synthetic path containment test")
    catalog.add_item(item)
    catalog.normalize_and_save(str(catalog_dir))
    catalog_path = catalog_dir / "catalog.json"

    try:
        assert_local_references_resolve(catalog_path)
    except AssertionError as error:
        assert "escapes generated output root" in str(error)
    else:
        raise AssertionError("External file URI unexpectedly passed local asset validation")


def test_item_bbox_crossing_antimeridian_is_valid(tmp_path):
    """A wrapped RFC 7946 bbox should contain coordinates on both sides of 180°."""
    document = {
        "type": "Feature",
        "id": "dateline-item",
        "geometry": {"type": "MultiPoint", "coordinates": [[179.5, 10.0], [-179.5, 10.5]]},
        "bbox": [179.0, 9.0, -179.0, 11.0],
        "properties": {"datetime": "2026-10-25T13:00:00Z"},
    }
    assert_item_spatiotemporal_consistency(document, tmp_path / "dateline-item.json")


def test_antimeridian_item_fits_wrapped_collection_extent(tmp_path):
    """A wrapped Item bbox inside a wider wrapped Collection extent is accepted."""
    item = {
        "id": "dateline-item",
        "bbox": [179.0, 9.0, -179.0, 11.0],
        "properties": {"datetime": "2026-10-25T13:00:00Z"},
    }
    collection = {
        "extent": {
            "spatial": {"bbox": [[170.0, 0.0, -170.0, 20.0]]},
            "temporal": {"interval": [["2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"]]},
        }
    }
    assert_item_within_collection_extent(item, collection, tmp_path / "dateline-item.json")


def test_item_outside_collection_spatial_extent_is_rejected(tmp_path):
    """A valid-looking Item bbox outside its Collection extent must fail validation."""
    item = {
        "id": "outside-item",
        "bbox": [-79.0, 30.0, -78.9, 30.1],
        "properties": {"datetime": "2026-10-25T13:00:00Z"},
    }
    collection = {
        "extent": {
            "spatial": {"bbox": [[-81.0, 28.0, -80.0, 29.0]]},
            "temporal": {"interval": [["2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"]]},
        }
    }
    try:
        assert_item_within_collection_extent(item, collection, tmp_path / "outside-item.json")
    except AssertionError as error:
        assert "outside Collection spatial extent" in str(error)
    else:
        raise AssertionError("Item outside Collection spatial extent unexpectedly passed validation")


def test_catalog_hierarchy_rejects_broken_local_child_link(tmp_path):
    """Local child links must resolve to an existing Catalog or Collection document."""
    root = tmp_path / "catalog"
    root.mkdir()
    catalog_path = root / "catalog.json"
    catalog_path.write_text(
        json.dumps(
            {
                "type": "Catalog",
                "id": "root",
                "links": [{"rel": "child", "href": "missing-collection/collection.json"}],
            }
        ),
        encoding="utf-8",
    )
    try:
        assert_catalog_hierarchy(catalog_path)
    except AssertionError as error:
        assert "does not resolve locally" in str(error)
    else:
        raise AssertionError("Broken local child link unexpectedly passed hierarchy validation")


def test_catalog_hierarchy_rejects_non_reciprocal_parent_child_links(tmp_path):
    """A child Catalog/Collection must point back to its parent."""
    root = tmp_path / "catalog"
    child_dir = root / "child"
    child_dir.mkdir(parents=True)
    catalog_path = root / "catalog.json"
    child_path = child_dir / "collection.json"
    catalog_path.write_text(
        json.dumps(
            {
                "type": "Catalog",
                "id": "root",
                "links": [{"rel": "child", "href": "child/collection.json"}],
            }
        ),
        encoding="utf-8",
    )
    child_path.write_text(
        json.dumps({"type": "Collection", "id": "child", "links": []}),
        encoding="utf-8",
    )
    try:
        assert_catalog_hierarchy(catalog_path)
    except AssertionError as error:
        assert "Non-reciprocal STAC hierarchy link" in str(error)
    else:
        raise AssertionError("Non-reciprocal hierarchy link unexpectedly passed validation")


def test_item_outside_collection_temporal_extent_is_rejected(tmp_path):
    """An Item timestamp outside the Collection interval must fail validation."""
    item = {
        "id": "outside-time-item",
        "bbox": [-80.8, 28.1, -80.7, 28.2],
        "properties": {"datetime": "2027-01-01T00:00:00Z"},
    }
    collection = {
        "extent": {
            "spatial": {"bbox": [[-81.0, 28.0, -80.0, 29.0]]},
            "temporal": {"interval": [["2026-01-01T00:00:00Z", "2026-12-31T23:59:59Z"]]},
        }
    }
    try:
        assert_item_within_collection_extent(item, collection, tmp_path / "outside-time-item.json")
    except AssertionError as error:
        assert "temporal range" in str(error)
        assert "falls outside Collection temporal extent" in str(error)
    else:
        raise AssertionError("Item outside Collection temporal extent unexpectedly passed validation")


def test_stac_validation_example_fails_closed_and_reports_both_cases(tmp_path):
    """The dedicated validation example must reject invalid data and exit successfully."""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, str(EXAMPLES_DIR / "09-stac-validation" / "run.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"STAC validation example failed with exit code {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Valid item: PASSED" in result.stdout
    assert "Invalid item: REJECTED as expected" in result.stdout
    assert "Datetime format: OK" in result.stdout
    assert "BBox validity: OK" in result.stdout

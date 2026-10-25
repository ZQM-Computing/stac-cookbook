"""Inventory, syntax, and offline runtime tests for the STAC cookbook."""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from pystac import STACObjectType
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
}
OFFLINE_STAC_EXAMPLES = (
    "01-catalog-creation",
    "02-item-validation",
    "05-cloud-deployment",
    "06-full-workflow",
    "11-bulk-operations",
    "12-stac-games",
)
EXPECTED_OUTPUT_MARKERS = {
    "01-catalog-creation": ("Catalog saved: zqm-demo-catalog", "Item: demo-item-1"),
    "02-item-validation": ("Item is valid STAC", "All required fields present"),
    "05-cloud-deployment": ("Catalog prepared for cloud deployment", "Catalog path: output/cloud_catalog"),
    "06-full-workflow": ("Catalog saved with 3 items", "Output: output/full_workflow"),
    "11-bulk-operations": ("Created 100 items", "Total items: 100"),
    "12-stac-games": ("Game locations: 6", "Content packs: 3"),
}
EXPECTED_CATALOGS = {
    "01-catalog-creation": ("catalog", "zqm-demo-catalog"),
    "05-cloud-deployment": ("cloud_catalog", "zqm-cloud-catalog"),
    "06-full-workflow": ("full_workflow", "zqm-full-workflow"),
    "11-bulk-operations": ("bulk_catalog", "bulk-catalog"),
    "12-stac-games": ("game_catalog", "zqm-labs-game-assets"),
}


def test_exact_example_inventory():
    """README's 12-example promise cannot silently regress to a partial tree."""
    scripts = sorted(EXAMPLES_DIR.glob("*/run.py"))
    actual = {path.parent.name for path in scripts}
    assert actual == EXPECTED_EXAMPLES, (
        f"Example inventory mismatch. Missing: {sorted(EXPECTED_EXAMPLES - actual)}; "
        f"unexpected: {sorted(actual - EXPECTED_EXAMPLES)}"
    )
    for script in scripts:
        assert script.stat().st_size > 0, f"Example entry point is empty: {script}"


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


def assert_item_spatiotemporal_consistency(document: dict, path: Path) -> None:
    """Check STAC Item geometry, bbox, and temporal metadata agree."""
    geometry = document.get("geometry")
    bbox = document.get("bbox")
    assert isinstance(geometry, dict) and geometry.get("type"), f"Missing GeoJSON geometry in {path}"
    assert isinstance(bbox, list) and len(bbox) in (4, 6), f"Invalid STAC Item bbox in {path}: {bbox}"
    assert all(isinstance(value, (int, float)) for value in bbox), f"Non-numeric STAC Item bbox in {path}: {bbox}"
    dimensions = len(bbox) // 2
    minima, maxima = bbox[:dimensions], bbox[dimensions:]
    assert all(low <= high for low, high in zip(minima, maxima)), f"Reversed STAC Item bbox in {path}: {bbox}"

    coordinates = list(_coordinate_pairs(geometry.get("coordinates")))
    assert coordinates, f"Geometry has no coordinate pairs in {path}"
    for longitude, latitude in coordinates:
        assert bbox[0] - 1e-9 <= longitude <= bbox[dimensions] + 1e-9, (
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
    if start is not None and end is not None:
        assert start <= end, f"Item start_datetime is after end_datetime in {path}: {start} > {end}"


def assert_collection_extent_consistency(document: dict, path: Path) -> None:
    """Check Collection spatial and temporal extent shapes and ordering."""
    extent = document.get("extent", {})
    spatial = extent.get("spatial", {}).get("bbox", [])
    temporal = extent.get("temporal", {}).get("interval", [])
    assert spatial, f"Collection has no spatial bbox extent in {path}"
    assert temporal, f"Collection has no temporal interval extent in {path}"

    for bbox in spatial:
        assert isinstance(bbox, list) and len(bbox) in (4, 6), f"Invalid Collection bbox in {path}: {bbox}"
        dimensions = len(bbox) // 2
        minima, maxima = bbox[:dimensions], bbox[dimensions:]
        assert all(isinstance(value, (int, float)) for value in bbox), f"Non-numeric Collection bbox in {path}: {bbox}"
        assert all(low <= high for low, high in zip(minima, maxima)), f"Reversed Collection bbox in {path}: {bbox}"

    for interval in temporal:
        assert isinstance(interval, list) and len(interval) == 2, (
            f"Invalid Collection temporal interval in {path}: {interval}"
        )
        start, end = interval
        assert start is None or end is None or start <= end, (
            f"Reversed Collection temporal interval in {path}: {interval}"
        )


def assert_local_references_resolve(catalog_path: Path) -> None:
    """Validate local STAC links and asset hrefs without making network requests."""
    root = catalog_path.parent
    documents = sorted(root.rglob("*.json"))
    assert documents, f"No JSON documents found under STAC output: {root}"

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
                target = Path(unquote(parsed.path))
            elif parsed.scheme:
                continue
            else:
                target = (document_path.parent / unquote(parsed.path)).resolve()
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
            assert target.is_file(), f"Broken local asset href for {asset_key!r} in {document_path}: {href}"



def assert_item_within_collection_extent(item: dict, collection: dict, path: Path) -> None:
    """Ensure an Item's spatial and temporal footprint fits its Collection extent."""
    item_bbox = item.get("bbox")
    spatial_extents = collection.get("extent", {}).get("spatial", {}).get("bbox", [])
    if isinstance(item_bbox, list) and spatial_extents:
        item_dimensions = len(item_bbox) // 2
        item_minima, item_maxima = item_bbox[:item_dimensions], item_bbox[item_dimensions:]
        assert len(item_bbox) in (4, 6), f"Invalid Item bbox in {path}: {item_bbox}"
        assert any(
            len(extent) in (4, 6)
            and all(
                extent[index] <= item_minima[index] + 1e-9
                and item_maxima[index] <= extent[index + len(extent) // 2] + 1e-9
                for index in range(2)
            )
            for extent in spatial_extents
        ), f"Item {item.get('id')!r} bbox {item_bbox} falls outside Collection spatial extent in {path}"

    def parse_datetime(value: str | None) -> object | None:
        if value is None:
            return None
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)

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

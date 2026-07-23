"""Generates static STAC catalog and collection JSON files for the
G02202 V6 sea ice concentration dataset.

Reads the GeoParquet files to derive the temporal extent, then writes:
  stac/catalog.json
  stac/sea-ice-concentration/collection.json

Run this after ingest.py to keep the catalog metadata current.
"""

from __future__ import annotations

import json
import sys
from typing import Any
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from stactools.noaa_cdr.sea_ice_concentration import stac as sic_stac  # noqa: E402

BASE_HREF = "https://noaadata.apps.nsidc.org/NOAA/G02202_V6/stac"
COLLECTION_ID = "noaa-cdr-sea-ice-concentration"

DAILY_PARQUET = Path(
    "stac/sea-ice-concentration/sea-ice-concentration-daily-items.parquet"
)
MONTHLY_PARQUET = Path(
    "stac/sea-ice-concentration/sea-ice-concentration-monthly-items.parquet"
)


def parquet_date_range(
    path: Path,
) -> tuple[datetime | None, datetime | None]:
    """Returns (start, end) datetime objects from start_datetime column, or (None, None)."""
    if not path.exists():
        return None, None
    table = pq.read_table(path, columns=["start_datetime"])
    col = table.column("start_datetime")
    if col.null_count == len(col):
        return None, None
    start = pc.min(col).as_py()
    end = pc.max(col).as_py()
    if start is not None and start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end is not None and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return start, end


def generate(output_dir: Path = Path("stac")) -> None:
    collection_dir = output_dir / "sea-ice-concentration"
    collection_dir.mkdir(parents=True, exist_ok=True)

    # Build collection from existing stactools create_collection()
    collection = sic_stac.create_collection()
    collection_href = f"{BASE_HREF}/sea-ice-concentration/collection.json"
    collection.set_self_href(collection_href)

    # Update temporal extent from actual GeoParquet contents
    daily_start, daily_end = parquet_date_range(DAILY_PARQUET)
    monthly_start, monthly_end = parquet_date_range(MONTHLY_PARQUET)
    starts = [s for s in [daily_start, monthly_start] if s]
    ends = [e for e in [daily_end, monthly_end] if e]
    if starts:
        collection.extent.temporal.intervals[0][0] = min(starts)
    if ends:
        collection.extent.temporal.intervals[0][1] = max(ends)

    # Add GeoParquet assets to the collection
    assets: dict[str, Any] = {}
    if DAILY_PARQUET.exists():
        assets["daily-items-geoparquet"] = {
            "href": f"{BASE_HREF}/sea-ice-concentration/sea-ice-concentration-daily-items.parquet",
            "type": "application/vnd.apache.parquet",
            "title": "Daily STAC Items (GeoParquet)",
            "description": (
                "All daily sea ice concentration STAC items in GeoParquet format. "
                "Filter by start_datetime, bbox, or noaa_cdr:hemisphere to find items."
            ),
            "roles": ["data", "stac-items"],
        }
    if MONTHLY_PARQUET.exists():
        assets["monthly-items-geoparquet"] = {
            "href": f"{BASE_HREF}/sea-ice-concentration/sea-ice-concentration-monthly-items.parquet",
            "type": "application/vnd.apache.parquet",
            "title": "Monthly STAC Items (GeoParquet)",
            "description": (
                "All monthly sea ice concentration STAC items in GeoParquet format. "
                "Filter by start_datetime, bbox, or noaa_cdr:hemisphere to find items."
            ),
            "roles": ["data", "stac-items"],
        }

    collection_dict = collection.to_dict()
    collection_dict["assets"] = assets
    collection_dict["links"] = [
        lnk
        for lnk in collection_dict.get("links", [])
        if lnk.get("rel") not in ("items", "item")
    ]
    collection_dict["links"].append(
        {"rel": "root", "href": f"{BASE_HREF}/catalog.json", "type": "application/json"}
    )

    collection_path = collection_dir / "collection.json"
    collection_path.write_text(json.dumps(collection_dict, indent=2))
    print(f"Wrote {collection_path}")

    # Write root catalog.json
    catalog = {
        "type": "Catalog",
        "id": "noaa-cdr",
        "stac_version": "1.0.0",
        "title": "NOAA Climate Data Records",
        "description": (
            "NOAA Climate Data Records (CDRs) are robust, sustainable, and "
            "scientifically defensible climate records that can be used to "
            "assess climate variability and change."
        ),
        "links": [
            {
                "rel": "self",
                "href": f"{BASE_HREF}/catalog.json",
                "type": "application/json",
            },
            {
                "rel": "root",
                "href": f"{BASE_HREF}/catalog.json",
                "type": "application/json",
            },
            {
                "rel": "child",
                "href": collection_href,
                "type": "application/json",
                "title": collection_dict.get("title", COLLECTION_ID),
            },
        ],
    }
    catalog_path = output_dir / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2))
    print(f"Wrote {catalog_path}")


if __name__ == "__main__":
    generate()

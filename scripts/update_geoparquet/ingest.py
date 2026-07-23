"""Scans the NSIDC HTTPS directory listing for new G02202 V6 daily and
monthly granules (both hemispheres), turns each into a STAC item using
the sea_ice_concentration stactools module, and appends them to STAC
GeoParquet files (one for daily, one for monthly).

Files are publicly accessible at noaadata.apps.nsidc.org with no
authentication required.

Designed to run on a schedule (see
.github/workflows/update-sea-ice-geoparquet.yml). Re-runs are safe:
granules already present in the GeoParquet (by item id) are skipped.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import requests
import stac_geoparquet.arrow as stac_geoparquet
from pystac import Item

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from stactools.noaa_cdr.sea_ice_concentration import stac as sic_stac  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("update_geoparquet")

BASE_URL = "https://noaadata.apps.nsidc.org/NOAA/G02202_V6"
HEMISPHERES = {
    "north": "psn25",
    "south": "pss25",
}
# Daily: sic_psn25_YYYYMMDD_<sensor>_v06r00.nc
DAILY_RE = re.compile(r"^sic_(psn25|pss25)_(\d{8})_[a-z0-9]+_v06r\d+\.nc$")
# Monthly: sic_psn25_YYYYMM_<sensor>_v06r00.nc
MONTHLY_RE = re.compile(r"^sic_(psn25|pss25)_(\d{6})_[a-z0-9]+_v06r\d+\.nc$")

DOWNLOAD_RETRIES = 5
CHECKPOINT_EVERY = 100


# ---------------------------------------------------------------------------
# Remote file listing
# ---------------------------------------------------------------------------


def iter_daily_files(
    hemisphere: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Iterator[tuple[str, str]]:
    """Yields (filename, url) for daily files, skipping years outside window."""
    token = HEMISPHERES[hemisphere]
    base = f"{BASE_URL}/{hemisphere}/daily"

    resp = requests.get(base + "/", timeout=30)
    resp.raise_for_status()
    years = sorted(set(re.findall(r'href="(\d{4})/"', resp.text)))

    since_year = since.year if since is not None else None
    until_year = until.year if until is not None else None
    for year in years:
        if since_year is not None and int(year) < since_year:
            continue
        if until_year is not None and int(year) > until_year:
            continue
        year_url = f"{base}/{year}/"
        resp = requests.get(year_url, timeout=30)
        resp.raise_for_status()
        filenames = re.findall(rf'href="(sic_{token}_\d{{8}}_[^"]+\.nc)"', resp.text)
        for fname in sorted(filenames):
            yield fname, f"{year_url}{fname}"


def iter_monthly_files(hemisphere: str) -> Iterator[tuple[str, str]]:
    """Yields (filename, url) for monthly files (flat directory, no year subdirs)."""
    token = HEMISPHERES[hemisphere]
    base = f"{BASE_URL}/{hemisphere}/monthly"

    resp = requests.get(base + "/", timeout=30)
    resp.raise_for_status()
    filenames = re.findall(rf'href="(sic_{token}_\d{{6}}_[^"]+\.nc)"', resp.text)
    for fname in sorted(filenames):
        yield fname, f"{base}/{fname}"


# ---------------------------------------------------------------------------
# GeoParquet helpers
# ---------------------------------------------------------------------------


def existing_item_ids(geoparquet_path: Path) -> set[str]:
    if not geoparquet_path.exists():
        return set()
    table = pq.read_table(geoparquet_path, columns=["id"])
    return set(table.column("id").to_pylist())


def latest_start_datetime(geoparquet_path: Path) -> Any:
    if not geoparquet_path.exists():
        return None
    table = pq.read_table(geoparquet_path, columns=["start_datetime"])
    col = table.column("start_datetime")
    if col.null_count == len(col):
        return None
    return pc.max(col).as_py()


def write_geoparquet(items: list[Item], geoparquet_path: Path) -> int:
    if not items:
        return 0
    new_table = stac_geoparquet.parse_stac_items_to_arrow(
        [item.to_dict() for item in items]
    ).read_all()
    if geoparquet_path.exists():
        existing_table = pq.read_table(geoparquet_path)
        # Reconcile column name differences between batches (e.g. proj:epsg
        # vs proj:code across stactools versions).
        existing_names = set(existing_table.schema.names)
        new_names = list(new_table.schema.names)
        missing_in_new = [n for n in existing_table.schema.names if n not in new_names]
        extra_in_new = [n for n in new_names if n not in existing_names]
        for old_name, new_name in zip(extra_in_new, missing_in_new):
            idx = new_table.schema.get_field_index(old_name)
            new_names[idx] = new_name
        new_table = new_table.rename_columns(new_names)
        combined = pa.concat_tables(
            [existing_table, new_table], promote_options="default"
        )
    else:
        geoparquet_path.parent.mkdir(parents=True, exist_ok=True)
        combined = new_table
    stac_geoparquet.to_parquet(combined, geoparquet_path)
    return len(items)


# ---------------------------------------------------------------------------
# Download + item building
# ---------------------------------------------------------------------------


def _download(session: requests.Session, url: str, dest: Path) -> None:
    """Download url to dest, retrying with exponential backoff on failure."""
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            with session.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
            return
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            if attempt == DOWNLOAD_RETRIES - 1:
                raise
            wait = 2**attempt
            logger.warning(
                "Download failed (%s), retrying in %ds (attempt %d/%d)...",
                e.__class__.__name__,
                wait,
                attempt + 1,
                DOWNLOAD_RETRIES,
            )
            time.sleep(wait)


def build_items(
    entries: list[tuple[str, str, str]],
    download_dir: Path,
    geoparquet_path: Path,
) -> int:
    """Download, build STAC items, flush to GeoParquet every CHECKPOINT_EVERY items.

    Returns total number of items added.
    """
    from stactools.noaa_cdr.constants import NETCDF_ASSET_KEY

    session = requests.Session()
    batch: list[Item] = []
    total_added = 0

    for fname, url, hemisphere in entries:
        local_path = download_dir / fname
        logger.info("Downloading %s", url)
        _download(session, url, local_path)

        item = sic_stac.create_item(str(local_path))
        item.properties["noaa_cdr:hemisphere"] = hemisphere
        item.assets[NETCDF_ASSET_KEY].href = url
        batch.append(item)
        logger.info("Built item %s (%s)", item.id, hemisphere)
        local_path.unlink()

        if len(batch) >= CHECKPOINT_EVERY:
            total_added += write_geoparquet(batch, geoparquet_path)
            logger.info(
                "Checkpoint: flushed %d items (%d total so far)",
                len(batch),
                total_added,
            )
            batch = []

    if batch:
        total_added += write_geoparquet(batch, geoparquet_path)

    return total_added


# ---------------------------------------------------------------------------
# Daily ingestion
# ---------------------------------------------------------------------------


def ingest_daily(
    geoparquet_path: Path,
    since: datetime | None = None,
    until: datetime | None = None,
) -> int:
    known_ids = existing_item_ids(geoparquet_path)
    logger.info("%d daily items already in %s", len(known_ids), geoparquet_path)

    if since is None:
        since = latest_start_datetime(geoparquet_path)

    entries = []
    for hemisphere in HEMISPHERES:
        for fname, url in iter_daily_files(hemisphere, since=since, until=until):
            item_id = fname[: -len(".nc")]
            if item_id in known_ids:
                continue
            m = DAILY_RE.match(fname)
            if m:
                file_date = datetime.strptime(m.group(2), "%Y%m%d").replace(
                    tzinfo=timezone.utc
                )
                if since is not None and file_date <= since:
                    continue
                if until is not None and file_date > until:
                    continue
            entries.append((fname, url, hemisphere))

    logger.info("%d new daily file(s) found", len(entries))
    with tempfile.TemporaryDirectory() as tmp:
        added = build_items(entries, Path(tmp), geoparquet_path)
    logger.info("Added %d new daily item(s)", added)
    return added


# ---------------------------------------------------------------------------
# Monthly ingestion
# ---------------------------------------------------------------------------


def ingest_monthly(geoparquet_path: Path) -> int:
    known_ids = existing_item_ids(geoparquet_path)
    logger.info("%d monthly items already in %s", len(known_ids), geoparquet_path)

    entries = []
    for hemisphere in HEMISPHERES:
        for fname, url in iter_monthly_files(hemisphere):
            item_id = fname[: -len(".nc")]
            if item_id in known_ids:
                continue
            entries.append((fname, url, hemisphere))

    logger.info("%d new monthly file(s) found", len(entries))
    with tempfile.TemporaryDirectory() as tmp:
        added = build_items(entries, Path(tmp), geoparquet_path)
    logger.info("Added %d new monthly item(s)", added)
    return added


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["daily", "monthly", "both"],
        default="daily",
        help="Which granule type to ingest (default: daily).",
    )
    parser.add_argument(
        "--daily-geoparquet",
        type=Path,
        default=Path(
            "stac/sea-ice-concentration/sea-ice-concentration-daily-items.parquet"
        ),
    )
    parser.add_argument(
        "--monthly-geoparquet",
        type=Path,
        default=Path(
            "stac/sea-ice-concentration/sea-ice-concentration-monthly-items.parquet"
        ),
    )
    parser.add_argument(
        "--since",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc),
        default=None,
        help="(daily only) Only ingest files after this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--until",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc),
        default=None,
        help="(daily only) Only ingest files on or before this date (YYYY-MM-DD).",
    )
    args = parser.parse_args()

    daily_added = 0
    monthly_added = 0

    if args.mode in ("daily", "both"):
        daily_added = ingest_daily(args.daily_geoparquet, args.since, args.until)

    if args.mode in ("monthly", "both"):
        monthly_added = ingest_monthly(args.monthly_geoparquet)

    print(f"daily_added={daily_added}")
    print(f"monthly_added={monthly_added}")


if __name__ == "__main__":
    main()

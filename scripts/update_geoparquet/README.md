# Sea ice concentration GeoParquet pipeline

Keeps `data/sea-ice-concentration-items.parquet` up to date with STAC items
for new G02202 V6 daily granules (both hemispheres), via a GitHub Actions
schedule (`.github/workflows/update-sea-ice-geoparquet.yml`).

## One-time setup

1. Add two repository secrets (Settings -> Secrets and variables -> Actions):
   - `EARTHDATA_USERNAME`
   - `EARTHDATA_PASSWORD`

   These need to belong to an Earthdata Login account that has accepted
   the NSIDC DAAC's EULA at least once (log in at
   <https://urs.earthdata.nasa.gov> and search for any NSIDC dataset once,
   if you haven't already).
2. Make sure the repo's default branch allows the `github-actions[bot]`
   user to push (this is the default for `permissions: contents: write`,
   but branch protection rules can override it).

## Running it manually

```bash
pip install -e .
pip install -r scripts/update_geoparquet/requirements.txt
export EARTHDATA_USERNAME=...
export EARTHDATA_PASSWORD=...
python scripts/update_geoparquet/ingest.py --geoparquet data/sea-ice-concentration-items.parquet
```

## How it decides what's "new"

It reads the `id` column already in the GeoParquet, searches CMR
(`earthaccess.search_data(short_name="G02202", version="6", ...)`) over a
21-day lookback window, and skips any granule whose item id (the filename
without `.nc`) is already present. This makes re-runs (including re-running
after a failed run) safe -- nothing is double-counted, and there's no
separate state file to get out of sync.

## Verification status

The item-creation and COG logic (`src/stactools/noaa_cdr/profile.py`,
`cog.py`, `sea_ice_concentration/*`) has been run against two real V6
sample files (one north, one south daily granule) and matches expected
shape/transform/classification metadata exactly. Filenames on those real
files do contain `_psn25_` / `_pss25_`, confirming `hemisphere_of()`'s
assumption. `raw_bt_seaice_conc`/`raw_nt_seaice_conc` were confirmed to
have no `flag_values` (so they're correctly excluded from
`VARIABLES_WITH_CLASSES`), and `crs` was confirmed to carry `GeoTransform`
but *not* `parent_grid_cell_row/column_subset_end` -- `_grid_geometry()`
in `profile.py` handles that combination explicitly now.

What's *not* yet verified, since it requires live network access this
environment didn't have:

- That `earthaccess.search_data(short_name="G02202", version="6", ...)`
  actually returns granules against live CMR (short_name/version are
  confirmed from NSIDC's public dataset pages, and the rest of the
  pipeline's logic -- dedup, item building, href-swapping, GeoParquet
  append -- was tested end to end with `earthaccess` mocked out).
- That `granule.data_links()` returns URLs in the form `hemisphere_of()`
  and the download/href-swap logic expect.

Do one manual run (`python scripts/update_geoparquet/ingest.py`) before
fully trusting the schedule, mainly to confirm those two CMR-facing points.

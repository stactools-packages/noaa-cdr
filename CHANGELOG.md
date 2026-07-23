# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project attempts to match the major and minor versions of
[stactools](https://github.com/stac-utils/stactools) and increments the patch
number as needed.

## [Unreleased]

### Added

- Summaries for the ocean heat content collection
  ([#50](https://github.com/stactools-packages/noaa-cdr/pull/50))
- `max_depth` to ocean heat content netcdf items
  ([#52](https://github.com/stactools-packages/noaa-cdr/pull/52))
- Aggregate examples for sea ice concentration, add `common_metadata` to items
- Support for NOAA/NSIDC Sea Ice Concentration CDR Version 6 (G02202 V6),
  including updated variable names, the new `cdr_supplementary` netCDF4 group,
  AMSR2 as an input source, and updated DOI/citation
- `cdr_melt_onset_day` and `surface_type_mask` assets (from `cdr_supplementary`
  group)
- 8-bit QA flag bitfield (V6 adds `No_input_data` and `melt_start_detected`
  bits)
- `classification:classes` for `cdr_seaice_conc_interp_temporal_flag` (31
  discrete enumerated values)
- `h5py` as an explicit dependency
- Daily and monthly STAC GeoParquet ingestion pipeline
  (`scripts/update_geoparquet/`)
- GitHub Actions workflow for automated daily GeoParquet updates
- Static STAC catalog and collection generation script
  (`scripts/update_geoparquet/generate_catalog.py`)

### Changed

- Use `application/x-netcdf` for media types instead of `application/netcdf`
  ([#55](https://github.com/stactools-packages/noaa-cdr/pull/55))
- `profile.py` grid geometry resolution now supports V6's `crs` variable
  (renamed from `projection`) and derives shape from `x`/`y` coordinate arrays
  when `parent_grid_cell_row/column_subset_end` attributes are absent
- `cog.py` merges `cdr_supplementary` netCDF4 group into root dataset before
  COG generation
- `surface_type_mask` replaces embedded land-mask flag values on
  `cdr_seaice_conc` (removed as of V5)
- Updated DOI to `10.7265/b18j-z797`, citation, and dataset homepage URL to V6

### Removed

- Spurious bitfield for sea ice concentration
  ([#53](https://github.com/stactools-packages/noaa-cdr/pull/53))
- `updated` from collections' item assets
  ([#54](https://github.com/stactools-packages/noaa-cdr/pull/54))
- V4 test fixtures (`seaice_conc_daily/monthly_nh/sh_*.nc`), replaced with
  real V6 sample files

## [0.2.1] - 2023-03-31

### Added

- Time intervals to NetCDF items and ocean heat content COG items ([#46](https://github.com/stactools-packages/noaa-cdr/pull/46))
- Max depth for ocean heat content ([#47](https://github.com/stactools-packages/noaa-cdr/pull/47))

## [0.2.0] - 2023-02-28

### Added

- `read_href_modifier` for ocean-heat-content ([#38](https://github.com/stactools-packages/noaa-cdr/pull/38))
- `cog_hrefs` argument for Ocean Heat Content's cogify, to allow skipping of COG
  creation ([#39](https://github.com/stactools-packages/noaa-cdr/pull/39))
- `decode_times` argument to `create_item` ([#40](https://github.com/stactools-packages/noaa-cdr/pull/40))
- Support for `time_coverage_duration` when creating items for NetCDFs ([#41](https://github.com/stactools-packages/noaa-cdr/pull/41))
- Raster extension to collections ([#43](https://github.com/stactools-packages/noaa-cdr/pull/43))

### Removed

- NetCDF assets from WHOI items ([#37](https://github.com/stactools-packages/noaa-cdr/pull/37))

## [0.1.0] - 2022-10-10

Initial release.

[Unreleased]: <https://github.com/stactools-packages/noaa-cdr/compare/v0.2.1..main>
[0.2.1]: <https://github.com/stactools-packages/noaa-cdr/compare/v0.2.0...v0.2.1>
[0.2.0]: <https://github.com/stactools-packages/noaa-cdr/compare/v0.1.0...v0.2.0>
[0.1.0]: <https://github.com/stactools-packages/noaa-cdr/releases/tag/v0.1.0>

<!-- markdownlint-disable-file MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project attempts to match the major and minor versions of
[stactools](https://github.com/stac-utils/stactools) and increments the patch
number as needed.

## [Unreleased]

### Added

- Summaries for the ocean heat content collection ([#50](https://github.com/stactools-packages/noaa-cdr/pull/50))
- `max_depth` to ocean heat content netcdf items ([#52](https://github.com/stactools-packages/noaa-cdr/pull/52))

### Changed

- Use `application/x-netcdf` for media types instead of `application/netcdf` ([#55](https://github.com/stactools-packages/noaa-cdr/pull/55))

### Removed

- Spurious bitfield for sea ice concentration ([#53](https://github.com/stactools-packages/noaa-cdr/pull/53))
- `updated` from collections' item assets ([#54](https://github.com/stactools-packages/noaa-cdr/pull/54))

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

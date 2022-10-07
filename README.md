# stactools-noaa-cdr

[![PyPI](https://img.shields.io/pypi/v/stactools-noaa-cdr)](https://pypi.org/project/stactools-noaa-cdr/)

- Name: noaa-cdr
- Package: `stactools.noaa_cdr`
- [stactools-noaa-cdr on PyPI](https://pypi.org/project/stactools-noaa-cdr/)
- Owner: @gadomski
- [Dataset homepage](https://www.ncei.noaa.gov/products/climate-data-records/)
- STAC extensions used:
  - [item assets](https://github.com/stac-extensions/item-assets)
  - [proj](https://github.com/stac-extensions/projection)
  - [raster](https://github.com/stac-extensions/raster)
  - [scientific](https://github.com/stac-extensions/scientific)
  - [classification](https://github.com/stac-extensions/classification)
- Extra fields: None
- [Browse the example in human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/noaa-cdr/main/examples/catalog.json)

## STAC Examples

- Collections
  - [Ocean heat content](examples/ocean-heat-content/collection.json)
- Items
  - [Ocean heat content, yearly for 2021, 2000m depth](examples/ocean-heat-content/ocean-heat-content-2021-2000m/ocean-heat-content-2021-2000m.json)

### Layout

Each Climate Data Record can have multiple subdatasets, which themselves can be
organized by time intervals and other attributes. We have chosen to create one
STAC collection for each CDR, and to organize items in that collection by time
interval and time window. Subdatasets are included as COG assets.

## Installation

```shell
pip install stactools-noaa-cdr
```

## Command-line Usage

To create a collection, e.g. for the [Ocean heat content CDR](https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content):

```sh
stac noaa-cdr ocean-heat-content create-collection examples/ocean-heat-content/collection.json
```

To create COGs and items:

```sh
stac noaa-cdr ocean-heat-content create-collection --create-items \
  examples/ocean-heat-content/collection.json
```

To only create COGs and items for the latest data (e.g. to create a small
example collection):

```sh
stac noaa-cdr ocean-heat-content create-collection --create-items --latest-only \
  examples/ocean-heat-content/collection.json
```

Each CDR has its own flavor of command line interface; use `stac noaa-cdr
--help` to see a list of supported CDRs.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

To check all files:

```shell
pre-commit run --all-files
```

To run the tests:

```shell
pytest
```

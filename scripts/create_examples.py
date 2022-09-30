#!/usr/bin/env python3

"""Creates the example STAC metadata (and COGs).

Assumptions:

- All ocean heat content products have been downloaded to a top level `data/`
  directory via the following command:

    stac noaa-cdr ocean-heat-content download data

- The test suite has been run, so all external data have been downloaded.
"""

import os.path
from pathlib import Path
from tempfile import TemporaryDirectory

import stactools.core.copy
from pystac import Catalog, CatalogType

from stactools.noaa_cdr.ocean_heat_content import stac as ocean_heat_content_stac
from stactools.noaa_cdr.sea_surface_temperature_optimum_interpolation import (
    stac as oisst_stac,
)

root = Path(__file__).parent.parent
examples = str(root / "examples")
untracked_data = str(root / "data")
external_data = str(root / "tests" / "data-files" / "external")

with TemporaryDirectory() as temporary_directory:
    catalog = Catalog("noaa-cdr", "NOAA CDR example catalog")

    print("Creating Ocean Heat Content collection...")
    ocean_heat_content = ocean_heat_content_stac.create_collection(
        cog_directory=temporary_directory,
        latest_only=True,
        local_directory=untracked_data,
    )
    catalog.add_child(ocean_heat_content)

    print("Creating Sea Surface Temperature Optimum Interpolation collection...")
    oisst = oisst_stac.create_collection()
    oisst_item = oisst_stac.create_item(
        os.path.join(external_data, "oisst-avhrr-v02r01.20220913.nc"),
        cogify=True,
        cog_directory=temporary_directory,
    )
    oisst.add_item(oisst_item)
    catalog.add_child(oisst)

    print("Saving catalog...")
    catalog.normalize_hrefs(examples)
    stactools.core.copy.move_all_assets(
        catalog, make_hrefs_relative=True, copy=True, ignore_conflicts=True
    )
    catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

    print("Done!")

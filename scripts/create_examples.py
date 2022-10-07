#!/usr/bin/env python3

"""Creates the example STAC metadata (and COGs).

Assumptions:

- All ocean heat content products have been downloaded to a top level `data/`
  directory via the following command:

    stac noaa-cdr ocean-heat-content download data

- The test suite has been run, so all external data have been downloaded.
"""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import stactools.core.copy
from pystac import Catalog, CatalogType

import stactools.noaa_cdr.stac
from stactools.noaa_cdr.ocean_heat_content import stac as ocean_heat_content_stac
from stactools.noaa_cdr.sea_ice_concentration import stac as sea_ice_concentration_stac
from stactools.noaa_cdr.sea_surface_temperature_optimum_interpolation import (
    stac as oisst_stac,
)
from stactools.noaa_cdr.sea_surface_temperature_whoi import stac as whoi_sst_stac

root = Path(__file__).parent.parent
examples = root / "examples"
untracked_data = root / "data"
data_files = root / "tests" / "data-files"
external_data = root / "tests" / "data-files" / "external"

description = (
    "NOAA's Climate Data Records (CDRs) are robust, sustainable, "
    "and scientifically sound climate records that provide trustworthy "
    "information on how, where, and to what extent the land, oceans, atmosphere "
    "and ice sheets are changing. These datasets are thoroughly vetted time "
    "series measurements with the longevity, consistency, and continuity to "
    "assess and measure climate variability and change. NOAA CDRs are vetted "
    "using standards established by the "
    "[National Research Council (NRC)]"
    "(http://www.nap.edu/catalog.php?record_id=10944).\n\n"
    "NOAA developed CDRs by applying modern data analysis methods to "
    "historical global satellite data. This process can clarify the "
    "underlying climate trends within the data and allows researchers "
    "and other users to identify economic and scientific value in these "
    "records. NCEI maintains and extends CDRs by applying the same methods "
    "to present-day and future satellite measurements.\n\n"
    "CDRs can be used to manage natural resources and agriculture, measure "
    "environmental impacts on human health and community preparedness, and "
    "inform policy development and decision making for other sectors and "
    "interest groups."
)

with TemporaryDirectory() as temporary_directory:
    catalog = Catalog("noaa-cdr", description, "Climate Data Records")

    print("Creating Ocean Heat Content collection...")
    ocean_heat_content = ocean_heat_content_stac.create_collection(
        cog_directory=temporary_directory,
        latest_only=True,
        local_directory=str(untracked_data),
    )
    catalog.add_child(ocean_heat_content)

    print("Creating Sea Surface Temperature Optimum Interpolation collection...")
    oisst = oisst_stac.create_collection()
    oisst_item = oisst_stac.create_item(
        str(external_data / "oisst-avhrr-v02r01.20220913.nc"),
    )
    oisst_item = stactools.noaa_cdr.stac.add_cogs(oisst_item, temporary_directory)
    oisst.add_item(oisst_item)
    catalog.add_child(oisst)

    print("Creating Sea Surface Temperature - WHOI collection...")
    whoi_sst = whoi_sst_stac.create_collection()
    whoi_sst_items = whoi_sst_stac.create_items(
        str(external_data / "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"),
        temporary_directory,
    )
    whoi_sst.add_items(whoi_sst_items)
    catalog.add_child(whoi_sst)

    print("Creating Sea Ice Concentration collection...")
    sea_ice_concentration = sea_ice_concentration_stac.create_collection()
    sea_ice_concentration_item = sea_ice_concentration_stac.create_item(
        str(data_files / "seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    )
    sea_ice_concentration_item = sea_ice_concentration_stac.add_cogs(
        sea_ice_concentration_item, temporary_directory
    )
    sea_ice_concentration.add_item(sea_ice_concentration_item)
    catalog.add_child(sea_ice_concentration)

    print("Saving catalog...")
    catalog.normalize_hrefs(str(examples))
    shutil.rmtree(examples)
    for item in catalog.get_all_items():
        for asset in item.assets.values():
            if asset.href.startswith(temporary_directory):
                href = stactools.core.copy.move_asset_file_to_item(
                    item, asset.href, copy=False
                )
                asset.href = href
        item.make_asset_hrefs_relative()
    catalog.save(catalog_type=CatalogType.SELF_CONTAINED)

    print("Done!")

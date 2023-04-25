#!/usr/bin/env python3

"""Creates the item asset JSON files for use in collections.

Assumptions:

- The test suite has been run, so all external data have been downloaded.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import orjson
from pystac import Item

import stactools.noaa_cdr.stac
from stactools.noaa_cdr.sea_ice_concentration import stac as sea_ice_stac
from stactools.noaa_cdr.sea_surface_temperature_optimum_interpolation import (
    stac as oisst_stac,
)
from stactools.noaa_cdr.sea_surface_temperature_whoi import stac as whoi_stac

root = Path(__file__).parent.parent
test_data = root / "tests" / "data-files"
external_test_data = test_data / "external"
src = root / "src" / "stactools" / "noaa_cdr"
sea_ice_data_path = test_data / "seaice_conc_daily_sh_20211231_f17_v04r00.nc"
sea_ice_item_assets_path = src / "sea_ice_concentration" / "item-assets.json"
oisst_data_path = external_test_data / "oisst-avhrr-v02r01.20220913.nc"
oisst_item_assets_path = (
    src / "sea_surface_temperature_optimum_interpolation" / "item-assets.json"
)
whoi_data_path = (
    external_test_data / "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
)
whoi_item_assets_path = src / "sea_surface_temperature_whoi" / "item-assets.json"


def write_item_assets(item: Item, path: Path) -> None:
    item_assets = {}
    for key, asset in item.assets.items():
        asset_dict = asset.to_dict()
        del asset_dict["href"]
        if "title" in asset_dict:
            del asset_dict["title"]
        if "description" in asset_dict:
            del asset_dict["description"]
        if "created" in asset_dict:
            del asset_dict["created"]
        if "updated" in asset_dict:
            del asset_dict["updated"]
        item_assets[key] = asset_dict
    with open(path, "w") as file:
        file.write(
            orjson.dumps(item_assets, option=orjson.OPT_INDENT_2).decode("utf-8")
        )


item = sea_ice_stac.create_item(str(sea_ice_data_path))
with TemporaryDirectory() as temporary_directory:
    item = sea_ice_stac.add_cogs(item, temporary_directory)
write_item_assets(item, sea_ice_item_assets_path)

item = oisst_stac.create_item(str(oisst_data_path))
with TemporaryDirectory() as temporary_directory:
    item = stactools.noaa_cdr.stac.add_cogs(item, temporary_directory)
write_item_assets(item, oisst_item_assets_path)

with TemporaryDirectory() as temporary_directory:
    items = whoi_stac.create_cog_items(str(whoi_data_path), temporary_directory)
write_item_assets(items[0], whoi_item_assets_path)

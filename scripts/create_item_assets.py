#!/usr/bin/env python3

"""Creates the item asset JSON files for use in collections."""

from pathlib import Path
from tempfile import TemporaryDirectory

import orjson

from stactools.noaa_cdr.sea_ice_concentration import stac

root = Path(__file__).parent.parent
test_data = root / "tests" / "data-files"
src = root / "src" / "stactools" / "noaa_cdr"
sea_ice_path = test_data / "seaice_conc_daily_sh_20211231_f17_v04r00.nc"

item = stac.create_item(str(sea_ice_path))
with TemporaryDirectory() as temporary_directory:
    item = stac.add_cogs(item, temporary_directory)
item_assets = {}
for key, asset in item.assets.items():
    asset_dict = asset.to_dict()
    del asset_dict["href"]
    if "created" in asset_dict:
        del asset_dict["created"]
    item_assets[key] = asset_dict

with open(src / "sea_ice_concentration" / "item-assets.json", "w") as file:
    file.write(orjson.dumps(item_assets, option=orjson.OPT_INDENT_2).decode("utf-8"))

import os.path
from typing import Optional

import dateutil.parser
import fsspec
import xarray
from pystac import Asset, Item
from pystac.extensions.projection import ProjectionExtension

from . import cog
from .constants import NETCDF_ASSET_KEY, PROCESSING_EXTENSION_SCHEMA
from .profile import DatasetProfile


def create_item(href: str, id: Optional[str] = None) -> Item:
    with fsspec.open(href) as file:
        with xarray.open_dataset(file) as ds:
            if id is None:
                if "id" in ds.attrs:
                    id = os.path.splitext(ds.id)[0]
                else:
                    id = os.path.splitext(os.path.basename(href))[0]
            profile = DatasetProfile.build(ds)
            item = Item(
                id=id,
                geometry=profile.geometry,
                bbox=profile.bbox,
                datetime=None,
                properties={
                    "start_datetime": ds.time_coverage_start,
                    "end_datetime": ds.time_coverage_end,
                },
            )
            item.stac_extensions.append(PROCESSING_EXTENSION_SCHEMA)
            item.properties["processing:level"] = f"L{ds.processing_level[-1]}"
            asset = Asset(
                href=href,
                title=f"{ds.title} NetCDF",
                description=ds.summary,
                media_type="application/netcdf",
                roles=["data"],
            )
            asset.common_metadata.created = dateutil.parser.parse(ds.date_created)
            if "date_modified" in ds.attrs:
                asset.common_metadata.updated = dateutil.parser.parse(ds.date_modified)
            item.assets[NETCDF_ASSET_KEY] = asset

            projection = ProjectionExtension.ext(item, add_if_missing=True)
            projection.epsg = profile.epsg
            if profile.wkt2:
                projection.wkt2 = profile.wkt2
            projection.shape = profile.shape
            projection.transform = list(profile.transform)[0:6]

    return item


def add_cogs(item: Item, directory: str) -> Item:
    href = item.assets[NETCDF_ASSET_KEY].href
    assets = cog.cogify(
        href,
        directory,
    )
    for key, value in assets.items():
        item.add_asset(key, value)
    return item

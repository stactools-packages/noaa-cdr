import os.path
from typing import Optional

import dateutil.parser
import fsspec
import xarray
from pystac import Asset, CatalogType, Collection, Item

from .. import time
from ..constants import (
    DEFAULT_CATALOG_TYPE,
    LICENSE,
    PROCESSING_EXTENSION_SCHEMA,
    PROVIDERS,
)
from . import cog
from .constants import BBOX, DESCRIPTION, EXTENT, GEOMETRY, ID, TITLE


def create_collection(catalog_type: CatalogType = DEFAULT_CATALOG_TYPE) -> Collection:
    return Collection(
        id=ID,
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=catalog_type,
        license=LICENSE,
        keywords=[],
        providers=PROVIDERS,
    )


def create_item(
    href: str, cogify: bool = False, cog_directory: Optional[str] = None
) -> Item:
    with fsspec.open(href) as file:
        with xarray.open_dataset(file) as ds:
            id = os.path.splitext(ds.id)[0]
            item = Item(
                id=id,
                geometry=GEOMETRY,
                bbox=BBOX,
                datetime=time.datetime64_to_datetime(ds.time.data[0]),
                properties={},
            )
            item.common_metadata.start_datetime = dateutil.parser.parse(
                ds.time_coverage_start
            )
            item.common_metadata.end_datetime = dateutil.parser.parse(
                ds.time_coverage_end
            )
            item.stac_extensions.append(PROCESSING_EXTENSION_SCHEMA)
            item.properties["processing:level"] = "L4"
            asset = Asset(
                href=href,
                title=f"{ds.title} NetCDF",
                description=ds.summary,
                media_type="application/netcdf",
                roles=["data"],
            )
            asset.common_metadata.created = dateutil.parser.parse(ds.date_created)
            asset.common_metadata.updated = dateutil.parser.parse(ds.date_modified)
            item.assets["netcdf"] = asset

    if cogify:
        assets = cog.cogify(href, cog_directory)
        for key, value in assets.items():
            item.add_asset(key, value)

    return item

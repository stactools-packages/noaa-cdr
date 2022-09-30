import copy
import os.path
from typing import Optional

import dateutil.parser
import fsspec
import xarray
from pystac import Asset, Collection, Item

from .. import dataset, time
from ..constants import (
    DEFAULT_CATALOG_TYPE,
    LICENSE,
    PROCESSING_EXTENSION_SCHEMA,
    PROVIDERS,
)
from .constants import BBOX, DESCRIPTION, EXTENT, GEOMETRY, ID, PROFILE, TITLE


def create_collection() -> Collection:
    return Collection(
        id=ID,
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=DEFAULT_CATALOG_TYPE,
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
                if not cog_directory:
                    cog_directory = os.path.basename(href)
                for variable in dataset.data_variable_names(ds):
                    ds[variable].assign_coords(lon=(((ds.lon + 180) % 360) - 180))
                    values = ds[variable].values.squeeze()
                    profile = copy.deepcopy(PROFILE)
                    profile.unit = ds[variable].units.replace("_", " ")
                    # TODO check datatype, scale, offset, and bounds
                    path = os.path.join(cog_directory, f"{id}-{variable}.tif")
                    asset = dataset.write_cog(
                        values,
                        path,
                        profile,
                    )
                    item.assets[variable] = asset

    return item

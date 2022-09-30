import copy
import datetime
import os.path
from typing import Optional

import dateutil.parser
import fsspec
import shapely.geometry
import xarray
from dateutil.tz import tzutc
from pystac import Asset, Item
from pystac.extensions.raster import DataType
from rasterio import Affine

from .. import dataset, time
from ..profile import Profile

BASE_DATETIME = datetime.datetime(1978, 1, 1, 12, 0, 0, tzinfo=tzutc())
BBOX = [-180.0, -90.0, 180.0, 90.0]
GEOMETRY = shapely.geometry.mapping(shapely.geometry.box(*BBOX))
PROCESSING_EXTENSION_SCHEMA = (
    "https://stac-extensions.github.io/processing/v1.1.0/schema.json"
)
PROFILE = Profile(
    width=1440,
    height=720,
    data_type=DataType.INT16,
    transform=Affine(0.25, 0.0, 0.0, 0.0, -0.25, 90.0),
    nodata=-999,
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

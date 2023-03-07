import os.path
from typing import Optional

import dateutil.parser
import fsspec
import pystac.utils
import xarray
from pystac import Asset, Item
from pystac.extensions.projection import ProjectionExtension

from . import cog
from .constants import (
    INTERVAL_ATTRIBUTE_NAME,
    NETCDF_ASSET_KEY,
    PROCESSING_EXTENSION_SCHEMA,
)
from .profile import DatasetProfile
from .time import TimeDuration, TimeResolution


def create_item(href: str, id: Optional[str] = None, decode_times: bool = True) -> Item:
    with fsspec.open(href) as file:
        with xarray.open_dataset(file, decode_times=decode_times) as ds:
            if id is None:
                if "id" in ds.attrs:
                    id = os.path.splitext(ds.id)[0]
                else:
                    id = os.path.splitext(os.path.basename(href))[0]
            profile = DatasetProfile.build(ds)
            if "time_coverage_start" in ds.attrs:
                if "time_coverage_end" in ds.attrs:
                    properties = {
                        "start_datetime": ds.time_coverage_start,
                        "end_datetime": ds.time_coverage_end,
                    }
                elif "time_coverage_duration" in ds.attrs:
                    time_duration = TimeDuration.parse(ds.time_coverage_duration)
                    start_datetime = dateutil.parser.parse(ds.time_coverage_start)
                    end_datetime = time_duration.end_datetime(start_datetime)
                    properties = {
                        "start_datetime": pystac.utils.datetime_to_str(start_datetime),
                        "end_datetime": pystac.utils.datetime_to_str(end_datetime),
                    }
            if "time_coverage_resolution" in ds.attrs:
                time_resolution = TimeResolution.from_value(ds.time_coverage_resolution)
                interval = time_resolution.to_interval()
            else:
                interval = None
            item = Item(
                id=id,
                geometry=profile.geometry,
                bbox=profile.bbox,
                datetime=None,
                properties=properties,
            )
            if interval:
                item.properties[INTERVAL_ATTRIBUTE_NAME] = interval
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

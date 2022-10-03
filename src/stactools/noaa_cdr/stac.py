import os.path

import dateutil.parser
import fsspec
import shapely.geometry
import xarray
from pyproj import CRS
from pyproj.enums import WktVersion
from pystac import Asset, Item
from pystac.extensions.projection import ProjectionExtension

from . import time
from .constants import PROCESSING_EXTENSION_SCHEMA


def create_item(href: str, remap_longitudes: bool = False) -> Item:
    with fsspec.open(href) as file:
        with xarray.open_dataset(file) as ds:
            id = os.path.splitext(ds.id)[0]
            xmin = float(ds.geospatial_lon_min)
            xmax = float(ds.geospatial_lon_max)
            if remap_longitudes and xmin == 0 and xmax == 360:
                xmin = -180
                xmax = 180
            ymin = float(ds.geospatial_lat_min)
            ymax = float(ds.geospatial_lat_max)
            bbox = [xmin, ymin, xmax, ymax]
            geometry = shapely.geometry.mapping(shapely.geometry.box(*bbox))
            item = Item(
                id=id,
                geometry=geometry,
                bbox=bbox,
                datetime=time.datetime64_to_datetime(ds.time.data[0]),
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
            item.assets["netcdf"] = asset

            projection = ProjectionExtension.ext(item, add_if_missing=True)
            if "projection" in ds.variables:
                # We can't use the spatial reference attribute, which is WKT,
                # because it doesn't parse valid for sea ice.
                projection.epsg = None
                crs = CRS(ds.projection.proj4text)
                projection.wkt2 = crs.to_wkt(WktVersion.WKT2_2019)
                projection.shape = [
                    int(ds.projection.parent_grid_cell_row_subset_end),
                    int(ds.projection.parent_grid_cell_column_subset_end),
                ]
                transform = list(
                    float(s) for s in ds.projection.GeoTransform.split(" ")
                )
                projection.transform = [
                    transform[1],
                    transform[2],
                    transform[0],
                    transform[4],
                    transform[5],
                    transform[3],
                ]
            else:
                projection.epsg = 4326
                projection.shape = [int(ds.sizes["lat"]), int(ds.sizes["lon"])]
                projection.transform = [
                    float(ds.geospatial_lon_resolution),
                    0,
                    xmin,
                    0,
                    -float(ds.geospatial_lat_resolution),
                    ymax,
                ]

    return item

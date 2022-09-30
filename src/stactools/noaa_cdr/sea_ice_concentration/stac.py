import os.path

import fsspec
import shapely.geometry
import xarray
from pystac import Item


def create_item(href: str) -> Item:
    with fsspec.open(href) as file:
        with xarray.open_dataset(file) as dataset:
            xmin = dataset.geospatial_lon_min
            xmax = dataset.geospatial_lon_max
            ymin = dataset.geospatial_lat_min
            ymax = dataset.geospatial_lat_max
            bbox = [xmin, ymin, xmax, ymax]
            geometry = shapely.geometry.mapping(shapely.geometry.box(*bbox))
            return Item(
                id=os.path.splitext(os.path.basename(href))[0],
                geometry=geometry,
                bbox=bbox,
                datetime=None,
                properties={
                    "start_datetime": dataset.time_coverage_start,
                    "end_datetime": dataset.time_coverage_end,
                },
            )

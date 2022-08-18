import datetime
import os.path
from dataclasses import dataclass
from typing import Any, Dict, Hashable, List, Optional

import fsspec
import numpy
import rasterio
import rasterio.shutil
import xarray
from rasterio import Affine, MemoryFile

from stactools.noaa_cdr import utils

from .constants import TimeResolution

BASE_TIME = datetime.datetime(1955, 1, 1)
GTIFF_PROFILE = {
    "crs": "epsg:4326",
    "width": 360,
    "height": 180,
    "dtype": "float32",
    "nodata": numpy.nan,
    "count": 1,
    "transform": Affine.from_gdal(-180, 1, 0, -90, 0, 1),
    "driver": "GTiff",
}
COG_PROFILE = {"compress": "deflate", "blocksize": 512, "driver": "COG"}


@dataclass(frozen=True)
class Cog:
    path: str
    time_resolution: TimeResolution
    datetime: datetime.datetime
    attributes: Dict[Hashable, Any]

    def time_interval_as_str(self) -> str:
        """Returns this COGs time resolution and datetime as a string.

        Returns:
            str: The time interval
        """
        return utils.time_interval_as_str(self.datetime, self.time_resolution)


def cogify(href: str, outdir: Optional[str] = None) -> List[Cog]:
    """Creates a Cloud-Optimized GeoTIFF from a CDR NetCDF.

    Args:
        href (str): Input NetCDF href.
        outdir (str, optional): Output directory for the COG. Defaults to None.
            If None, the COG will be created alongside the input NetCDF. If href
            is a url and outdir is not provided, an Exception is raised.

    Returns:
        Cog: The created Cog.
    """
    if outdir is None:
        if href.startswith("http"):
            raise ValueError(f"Output directory is required for http hrefs: {href}")
        outdir = os.path.dirname(href)
    cogs = list()
    with fsspec.open(href) as file:
        with xarray.open_dataset(file, decode_times=False) as dataset:
            time_resolution = TimeResolution.from_value(
                dataset.time_coverage_resolution
            )
            variable = utils.data_variable_name(dataset)
            for i, month_offset in enumerate(dataset[variable].time):
                time = utils.add_months_to_datetime(BASE_TIME, month_offset)
                suffix = utils.time_interval_as_str(time, time_resolution)
                output_path = os.path.join(
                    outdir,
                    f"{os.path.splitext(os.path.basename(href))[0]}_{suffix}.tif",
                )
                values = dataset[variable].isel(time=i).values.squeeze()
                with MemoryFile() as memory_file:
                    with memory_file.open(**GTIFF_PROFILE) as open_memory_file:
                        open_memory_file.write(values, 1)
                        # TODO save the month offset and time resolution in the TIFF
                        # tags for later discovery
                        rasterio.shutil.copy(
                            open_memory_file, output_path, **COG_PROFILE
                        )
                cogs.append(Cog(output_path, time_resolution, time, dataset.attrs))
    return cogs

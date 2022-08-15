import datetime
import os.path
from typing import List, Optional

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


def cogify(path: str, outdir: Optional[str] = None) -> List[str]:
    """Creates a Cloud-Optimized GeoTIFF from a CDR NetCDF.

    Args:
        path (str): Input NetCDF path.
        outdir (str, optional): Output directory for the COG. Defaults to None.
            If None, the COG will be created alongside the input NetCDF.

    Returns:
        str: The path of the COG.
    """
    if outdir is None:
        outdir = os.path.dirname(path)
    output_paths = list()
    with xarray.open_dataset(path, decode_times=False) as dataset:
        time_resolution = next(
            (t for t in TimeResolution if t.value == dataset.time_coverage_resolution),
            None,
        )
        if time_resolution is None:
            raise Exception(
                "Encountered unexpected time_coverage_resolution: "
                f"{dataset.time_coverage_resolution}"
            )
        for i, month_offset in enumerate(dataset.h18_hc.time):
            time = utils.add_months_to_datetime(BASE_TIME, month_offset)
            suffix = utils.time_interval_as_str(time, time_resolution)
            output_path = os.path.join(
                outdir, f"{os.path.splitext(os.path.basename(path))[0]}_{suffix}.tif"
            )
            # TODO learn the variable name from the netcdf metadata
            values = dataset.h18_hc.isel(time=i).values.squeeze()
            with MemoryFile() as memory_file:
                with memory_file.open(**GTIFF_PROFILE) as open_memory_file:
                    open_memory_file.write(values, 1)
                    # TODO save the month offset and time resolution in the TIFF
                    # tags for later discovery
                    rasterio.shutil.copy(open_memory_file, output_path, **COG_PROFILE)
            output_paths.append(output_path)
    return output_paths

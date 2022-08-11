import datetime
import os.path
from typing import List, Optional

import dateutil.relativedelta
import numpy
import rasterio
import rasterio.shutil
import xarray
from rasterio import Affine, MemoryFile

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
        for i, month_offset in enumerate(dataset.h18_hc.time):
            time = BASE_TIME + dateutil.relativedelta.relativedelta(months=month_offset)
            year = time.year
            output_path = os.path.join(
                outdir, f"{os.path.splitext(os.path.basename(path))[0]}_{year}.tif"
            )
            values = dataset.h18_hc.isel(time=i).values.squeeze()
            with MemoryFile() as memory_file:
                with memory_file.open(**GTIFF_PROFILE) as open_memory_file:
                    open_memory_file.write(values, 1)
                    rasterio.shutil.copy(open_memory_file, output_path, **COG_PROFILE)
            output_paths.append(output_path)
    return output_paths

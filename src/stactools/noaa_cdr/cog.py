import os
from typing import Any, Dict, Type

import fsspec
import numpy
import rasterio.shutil
import xarray
from numpy.typing import NDArray
from pystac import Asset
from rasterio import MemoryFile

from . import dataset
from .profile import BandProfile


def cogify(
    path: str,
    directory: str,
    band_profile_class: Type[BandProfile] = BandProfile,
) -> Dict[str, Asset]:
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(path))[0]
    assets = dict()
    with fsspec.open(path) as file:
        with xarray.open_dataset(file, mask_and_scale=False) as ds:
            for variable in dataset.data_variable_names(ds):
                profile = band_profile_class.build(ds, variable)
                data = ds[variable]
                values = data.values.squeeze()
                if profile.needs_vertical_flip:
                    values = numpy.flipud(values)
                if profile.needs_longitude_remap:
                    values = numpy.roll(values, int(profile.width / 2), 1)
                path = os.path.join(directory, f"{file_name}-{variable}.tif")
                write(
                    values,
                    path,
                    profile,
                )
                assets[variable] = profile.cog_asset(path)
    return assets


def write(
    values: NDArray[Any],
    path: str,
    profile: BandProfile,
) -> None:
    with MemoryFile() as memory_file:
        with memory_file.open(**profile.gtiff()) as open_memory_file:
            open_memory_file.write(values, 1)
            rasterio.shutil.copy(open_memory_file, path, **profile.cog())

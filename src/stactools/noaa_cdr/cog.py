import os
from typing import Any, Dict, Type

import fsspec
import numpy
import rasterio.shutil
import xarray
from pystac import Asset
from rasterio import MemoryFile

from . import dataset
from .profile import BandProfile

# Variables that moved into this netCDF4 group in sea ice concentration V6
# (raw_bt_seaice_conc, raw_nt_seaice_conc, surface_type_mask,
# cdr_melt_onset_day, latitude, longitude). Other CDRs don't have this group,
# so we just no-op if it's missing.
SUPPLEMENTARY_GROUP = "cdr_supplementary"


def _open_with_groups(file: Any) -> xarray.Dataset:
    """Opens the root group, and merges in the cdr_supplementary group if
    present, so all data variables are visible on one Dataset regardless of
    which netCDF4 group they live in."""
    root = xarray.open_dataset(file, mask_and_scale=False)
    try:
        supplementary = xarray.open_dataset(
            file, group=SUPPLEMENTARY_GROUP, mask_and_scale=False
        )
    except OSError:
        # Group doesn't exist on this file -- not a V6 sea ice file, or an
        # older revision without cdr_supplementary. Nothing to merge.
        return root
    return xarray.merge([root, supplementary], compat="override", join="override")


def cogify(
    path: str,
    directory: str,
    band_profile_class: Type[BandProfile] = BandProfile,
) -> Dict[str, Asset]:
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(path))[0]
    assets = dict()
    with fsspec.open(path) as file:
        with _open_with_groups(file) as ds:
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
    values: numpy.ndarray[Any, Any],
    path: str,
    profile: BandProfile,
) -> None:
    with MemoryFile() as memory_file:
        with memory_file.open(**profile.gtiff()) as open_memory_file:
            open_memory_file.write(values, 1)
            rasterio.shutil.copy(open_memory_file, path, **profile.cog())

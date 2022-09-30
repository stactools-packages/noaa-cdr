import copy
import os
from typing import Dict, Optional

import fsspec
import xarray
from pystac import Asset

from . import dataset
from .profile import Profile


def cogify(path: str, profile: Profile, directory: Optional[str]) -> Dict[str, Asset]:
    """Creates COGs for each COG-able variable in a NetCDF file.

    COG-able variables are found using :py:func:`dataset.data_variable_names`.
    """
    if not directory:
        directory = os.path.basename(path)
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(path))[0]
    assets = dict()
    with fsspec.open(path) as file:
        with xarray.open_dataset(file) as ds:
            for variable in dataset.data_variable_names(ds):
                values = ds[variable].values.squeeze()
                profile = copy.deepcopy(profile)
                profile.unit = ds[variable].units.replace("_", " ")
                path = os.path.join(directory, f"{file_name}-{variable}.tif")
                asset = dataset.write_cog(
                    values,
                    path,
                    profile,
                )
                assets[variable] = asset
    return assets

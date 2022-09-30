import copy
import os
from typing import Dict, Optional

import fsspec
import xarray
from pystac import Asset

from .. import dataset
from .constants import PROFILE


def cogify(path: str, directory: Optional[str]) -> Dict[str, Asset]:
    if not directory:
        directory = os.path.basename(path)
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(path))[0]
    assets = dict()
    with fsspec.open(path) as file:
        with xarray.open_dataset(file) as ds:
            for variable in dataset.data_variable_names(ds):
                ds[variable].assign_coords(lon=(((ds.lon + 180) % 360) - 180))
                values = ds[variable].values.squeeze()
                profile = copy.deepcopy(PROFILE)
                profile.unit = ds[variable].units.replace("_", " ")
                # TODO check datatype, scale, offset, and bounds
                path = os.path.join(directory, f"{file_name}-{variable}.tif")
                asset = dataset.write_cog(
                    values,
                    path,
                    profile,
                )
                assets[variable] = asset
    return assets

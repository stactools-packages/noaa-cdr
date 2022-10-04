import os
from typing import Dict

import fsspec
import xarray
from pystac import Asset

from . import dataset
from .profile import BandProfile


def cogify(path: str, directory: str) -> Dict[str, Asset]:
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.splitext(os.path.basename(path))[0]
    assets = dict()
    with fsspec.open(path) as file:
        with xarray.open_dataset(file, mask_and_scale=False) as ds:
            for variable in dataset.data_variable_names(ds):
                # TODO remap > 180 longitudes
                profile = BandProfile.build(ds, variable)
                values = ds[variable].values.squeeze()
                path = os.path.join(directory, f"{file_name}-{variable}.tif")
                asset = dataset.write_cog(
                    values,
                    path,
                    profile,
                )
                assets[variable] = asset
    return assets

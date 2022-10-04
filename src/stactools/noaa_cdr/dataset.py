from typing import Any, List

import rasterio.shutil
from numpy.typing import NDArray
from pystac import Asset, MediaType
from rasterio import MemoryFile
from xarray import Dataset

from .profile import BandProfile


def data_variable_name(dataset: Dataset) -> str:
    """Returns the variable name that points to a four-dimensional data array.
    Args:
        dataset (xarray.Dataset): An open xarray Dataset
    Returns:
        str: The variable name.
    """
    names = list(data_variable_names(dataset))
    if not names:
        raise ValueError("No 4-dimensional variable found in this dataset.")
    elif len(names) == 1:
        return names[0]
    else:
        raise ValueError(
            f"Multiple 4-dimensional variables found in this dataset: {names}"
        )


def data_variable_names(dataset: Dataset) -> List[str]:
    """Returns a list of the variable names that point to a
    four-dimensional data array.

    Args:
        dataset (xarray.Dataset): An open xarray Dataset
    Returns:
        List[str]: List of the variable names.
    """
    return list(
        str(variable)
        for variable in dataset.variables
        if len(dataset[variable].sizes) == 4
    )


def write_cog(
    values: NDArray[Any],
    path: str,
    profile: BandProfile,
) -> Asset:
    with MemoryFile() as memory_file:
        with memory_file.open(**profile.gtiff()) as open_memory_file:
            open_memory_file.write(values, 1)
            rasterio.shutil.copy(open_memory_file, path, **profile.cog())
    asset = Asset(href=path, media_type=MediaType.COG, roles=["data"])
    asset.extra_fields["raster:bands"] = [profile.raster_band().to_dict()]
    return asset

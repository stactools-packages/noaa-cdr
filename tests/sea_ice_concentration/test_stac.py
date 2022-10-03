from typing import List

import pyproj
import pytest
from pystac.extensions.projection import ProjectionExtension

from stactools.noaa_cdr.sea_ice_concentration import stac

from .. import test_data


@pytest.mark.parametrize(
    "file_name,shape,transform",
    [
        (
            "seaice_conc_daily_nh_20211231_f17_v04r00.nc",
            [448, 304],
            [25000.0, 0.0, -3850000.0, 0.0, -25000.0, 5850000.0],
        ),
        (
            "seaice_conc_daily_sh_20211231_f17_v04r00.nc",
            [332, 316],
            [25000.0, 0.0, -3950000.0, 0.0, -25000.0, 4350000.0],
        ),
        (
            "seaice_conc_monthly_nh_202112_f17_v04r00.nc",
            [448, 304],
            [25000.0, 0.0, -3850000.0, 0.0, -25000.0, 5850000.0],
        ),
        (
            "seaice_conc_monthly_sh_202112_f17_v04r00.nc",
            [332, 316],
            [25000.0, 0.0, -3950000.0, 0.0, -25000.0, 4350000.0],
        ),
    ],
)
def test_create_item(file_name: str, shape: List[int], transform: List[float]) -> None:
    path = test_data.get_path(f"data-files/{file_name}")
    item = stac.create_item(path)

    projection = ProjectionExtension.ext(item)
    _ = pyproj.CRS(projection.wkt2)
    assert projection.shape == shape
    assert projection.transform == transform

    item.validate()
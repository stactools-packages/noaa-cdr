from pathlib import Path
from typing import List

import pyproj
import pytest
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension
from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr.constants import CLASSIFICATION_EXTENSION_SCHEMA
from stactools.noaa_cdr.sea_ice_concentration import cog, stac

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
    assert item.id == Path(file_name).stem
    assert item.datetime is None

    projection = ProjectionExtension.ext(item)
    _ = pyproj.CRS(projection.wkt2)
    assert projection.shape == shape
    assert projection.transform == transform

    item.validate()


def test_add_cogs(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    item = stac.create_item(path)
    item = stac.add_cogs(item, str(tmp_path))
    assert CLASSIFICATION_EXTENSION_SCHEMA in item.stac_extensions


def test_cogify(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    assets = cog.cogify(path, str(tmp_path))
    assert len(assets) == 8
    for asset in assets.values():
        assert asset.extra_fields["raster:bands"][0]["spatial_resolution"]
    for key in [
        "cdr_seaice_conc",
        "nsidc_bt_seaice_conc",
        "stdev_of_cdr_seaice_conc",
        "temporal_interpolation_flag",
    ]:
        asset = assets[key]
        assert "classification:classes" in asset.extra_fields

    for key in ["qa_of_cdr_seaice_conc", "spatial_interpolation_flag"]:
        asset = assets[key]
        assert "classification:bitfields" in asset.extra_fields


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.id == "noaa-cdr-sea-ice-concentration"

    scientific = ScientificExtension.ext(collection)
    assert scientific.doi == "10.7265/efmz-2t65"
    assert scientific.citation

    RasterExtension.validate_has_extension(collection, add_if_missing=False)

    collection.set_self_href("")
    collection.validate()


def test_unitless(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    assets = cog.cogify(path, str(tmp_path))
    assert "unit" not in assets["cdr_seaice_conc"].extra_fields["raster:bands"][0]

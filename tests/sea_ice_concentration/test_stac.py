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
            # Real V6 sample file. Its `crs` variable carries GeoTransform
            # but NOT parent_grid_cell_row/column_subset_end (V4 had both;
            # V6 dropped the latter) -- this exercises that exact path.
            "sic_psn25_19850130_n07_v06r00.nc",
            [448, 304],
            [25000.0, 0.0, -3850000.0, 0.0, -25000.0, 5850000.0],
        ),
        (
            "sic_pss25_19810105_n07_v06r00.nc",
            [332, 316],
            [25000.0, 0.0, -3950000.0, 0.0, -25000.0, 4350000.0],
        ),
        (
            # Synthetic file with no GeoTransform attr at all, to exercise
            # the full x/y coordinate-array fallback path -- not currently
            # needed by real V6 files, but kept as forward-looking
            # robustness coverage in case that attribute is dropped too.
            "sic_psn25_20260209_am2_v06r00_no_geotransform.nc",
            [448, 304],
            [25000.0, 0.0, -3850000.0, 0.0, -25000.0, 5850000.0],
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
    path = test_data.get_path("data-files/sic_psn25_19850130_n07_v06r00.nc")
    item = stac.create_item(path)
    item = stac.add_cogs(item, str(tmp_path))
    assert CLASSIFICATION_EXTENSION_SCHEMA in item.stac_extensions


def test_cogify(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/sic_psn25_19850130_n07_v06r00.nc")
    assets = cog.cogify(path, str(tmp_path))
    # cdr_seaice_conc, raw_bt_seaice_conc, raw_nt_seaice_conc,
    # cdr_seaice_conc_qa_flag, cdr_seaice_conc_interp_spatial_flag,
    # cdr_seaice_conc_interp_temporal_flag, cdr_seaice_conc_stdev,
    # cdr_melt_onset_day, surface_type_mask
    # (south hemisphere files have 8 -- no cdr_melt_onset_day)
    assert len(assets) == 9
    for asset in assets.values():
        assert asset.extra_fields["raster:bands"][0]["spatial_resolution"]
    for key in ["surface_type_mask", "cdr_seaice_conc_interp_temporal_flag"]:
        asset = assets[key]
        assert "classification:classes" in asset.extra_fields

    for key in ["cdr_seaice_conc_qa_flag", "cdr_seaice_conc_interp_spatial_flag"]:
        asset = assets[key]
        assert "classification:bitfields" in asset.extra_fields


def test_cogify_south(tmp_path: Path) -> None:
    # South hemisphere files don't have cdr_melt_onset_day.
    path = test_data.get_path("data-files/sic_pss25_19810105_n07_v06r00.nc")
    assets = cog.cogify(path, str(tmp_path))
    assert len(assets) == 8
    assert "cdr_melt_onset_day" not in assets


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.id == "noaa-cdr-sea-ice-concentration"

    scientific = ScientificExtension.ext(collection)
    assert scientific.doi == "10.7265/b18j-z797"
    assert scientific.citation

    RasterExtension.validate_has_extension(collection, add_if_missing=False)

    collection.set_self_href("")
    collection.validate()


def test_unitless(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/sic_psn25_19850130_n07_v06r00.nc")
    assets = cog.cogify(path, str(tmp_path))
    assert "unit" not in assets["cdr_seaice_conc"].extra_fields["raster:bands"][0]

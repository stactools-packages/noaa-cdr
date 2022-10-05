import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dateutil.tz import tzutc
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension
from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr.ocean_heat_content import cog, stac

from .. import test_data


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.id == "noaa-cdr-ocean-heat-content"
    assert len(collection.assets) == 44
    for asset in collection.assets.values():
        assert asset.title is not None
        assert asset.description is not None
        assert asset.media_type == "application/netcdf"
        assert asset.roles == ["data"]

    scientific = ScientificExtension.ext(collection)
    assert scientific.doi == "10.7289/v53f4mvp"
    assert scientific.citation

    collection.set_self_href("")
    collection.validate_all()


def test_create_items_one_netcdf() -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    with TemporaryDirectory() as temporary_directory:
        items = stac.create_items([path], temporary_directory)
    assert len(items) == 17
    for item in items:
        assert len(item.assets) == 1
        assert item.datetime
        year = item.datetime.year
        assert item.common_metadata.start_datetime == datetime.datetime(
            year, 1, 1, tzinfo=tzutc()
        )
        assert item.common_metadata.end_datetime == datetime.datetime(
            year, 12, 31, 23, 59, 59, tzinfo=tzutc()
        )
        assert item.common_metadata.updated is None

        proj = ProjectionExtension.ext(item)
        assert proj.epsg == 4326
        assert proj.shape == [180, 360]
        assert proj.transform == [1.0, 0, -180, 0, -1, 90]

        for asset in item.assets.values():
            raster = RasterExtension.ext(asset)
            assert raster.bands
            assert len(raster.bands) == 1
            band = raster.bands[0]
            assert band.nodata == "nan"
            assert band.data_type == "float32"
            assert band.unit == "10^18 joules"

        item.validate()


def test_create_items_two_netcdfs_same_items(tmp_path: Path) -> None:
    paths = [
        test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc"),
        test_data.get_external_data(
            "mean_halosteric_sea_level_anomaly_0-2000_yearly.nc"
        ),
    ]
    items = stac.create_items(paths, str(tmp_path))
    assert len(items) == 17
    for item in items:
        assert len(item.assets) == 2
        item.validate()


def test_create_items_two_netcdfs_different_items() -> None:
    paths = [
        test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc"),
        test_data.get_external_data(
            "mean_halosteric_sea_level_anomaly_0-2000_pentad.nc"
        ),
    ]
    with TemporaryDirectory() as temporary_directory:
        items = stac.create_items(paths, temporary_directory)
    assert len(items) == 80
    for item in items:
        assert len(item.assets) == 1
        item.validate()


def test_create_items_one_netcdf_latest_only(tmp_path: Path) -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    items = stac.create_items([path], str(tmp_path), latest_only=True)
    assert len(items) == 1
    items[0].validate()


@pytest.mark.parametrize(
    "infile,num_cogs",
    [
        ("heat_content_anomaly_0-700_yearly.nc", 67),
        ("heat_content_anomaly_0-2000_monthly.nc", 207),
        ("heat_content_anomaly_0-2000_pentad.nc", 63),
        ("heat_content_anomaly_0-2000_seasonal.nc", 69),
        ("heat_content_anomaly_0-2000_yearly.nc", 17),
        ("mean_halosteric_sea_level_anomaly_0-2000_yearly.nc", 17),
        ("mean_salinity_anomaly_0-2000_yearly.nc", 17),
        ("mean_temperature_anomaly_0-2000_yearly.nc", 17),
        ("mean_thermosteric_sea_level_anomaly_0-2000_yearly.nc", 17),
        ("mean_total_steric_sea_level_anomaly_0-2000_yearly.nc", 17),
    ],
)
def test_cogify(tmp_path: Path, infile: str, num_cogs: int) -> None:
    external_data_path = test_data.get_external_data(infile)
    cogs = cog.cogify(external_data_path, str(tmp_path))
    assert len(cogs) == num_cogs
    for c in cogs:
        assert Path(c.asset.href).exists()


def test_cogify_href(tmp_path: Path) -> None:
    href = (
        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data"
        "/0164586/derived/heat_content_anomaly_0-2000_yearly.nc"
    )
    cogs = cog.cogify(href, str(tmp_path))
    assert len(cogs) == 17
    for c in cogs:
        assert Path(c.asset.href).exists()


def test_cogify_href_no_output_directory() -> None:
    href = (
        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data"
        "/0164586/derived/heat_content_anomaly_0-2000_yearly.nc"
    )
    with pytest.raises(Exception):
        cog.cogify(href)

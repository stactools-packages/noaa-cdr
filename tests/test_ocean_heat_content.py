import datetime
import os.path
from tempfile import TemporaryDirectory

import pytest
from dateutil.tz import tzutc
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension
from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr import ocean_heat_content

from . import test_data


def test_create_collection() -> None:
    collection = ocean_heat_content.create_collection()
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
        items = ocean_heat_content.create_items([path], temporary_directory)
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
        assert item.common_metadata.created
        assert item.common_metadata.updated is None

        proj = ProjectionExtension.ext(item)
        assert proj.epsg == 4326
        assert proj.shape == [180, 360]
        assert proj.transform == [-180, 1.0, 0.0, -90.0, 0.0, 1.0]

        for asset in item.assets.values():
            raster = RasterExtension.ext(asset)
            assert raster.bands
            assert len(raster.bands) == 1
            band = raster.bands[0]
            assert band.nodata == "nan"
            assert band.data_type == "float32"
            assert band.unit == "10^18 joules"

        item.validate()


def test_create_items_two_netcdfs_same_items() -> None:
    paths = [
        test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc"),
        test_data.get_external_data(
            "mean_halosteric_sea_level_anomaly_0-2000_yearly.nc"
        ),
    ]
    with TemporaryDirectory() as temporary_directory:
        items = ocean_heat_content.create_items(paths, temporary_directory)
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
        items = ocean_heat_content.create_items(paths, temporary_directory)
    assert len(items) == 80
    for item in items:
        assert len(item.assets) == 1
        item.validate()


def test_create_items_one_netcdf_latest_only() -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    with TemporaryDirectory() as temporary_directory:
        items = ocean_heat_content.create_items(
            [path], temporary_directory, latest_only=True
        )
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
def test_cogify(infile: str, num_cogs: int) -> None:
    external_data_path = test_data.get_external_data(infile)
    with TemporaryDirectory() as temporary_directory:
        cogs = ocean_heat_content.cogify(external_data_path, temporary_directory)
        assert len(cogs) == num_cogs
        for cog in cogs:
            assert os.path.exists(cog.asset.href)


def test_cogify_href() -> None:
    href = (
        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data"
        "/0164586/derived/heat_content_anomaly_0-2000_yearly.nc"
    )
    with TemporaryDirectory() as temporary_directory:
        cogs = ocean_heat_content.cogify(href, temporary_directory)
        assert len(cogs) == 17
        for cog in cogs:
            assert os.path.exists(cog.asset.href)


def test_cogify_href_no_output_directory() -> None:
    href = (
        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data"
        "/0164586/derived/heat_content_anomaly_0-2000_yearly.nc"
    )
    with pytest.raises(Exception):
        ocean_heat_content.cogify(href)

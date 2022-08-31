import datetime
from tempfile import TemporaryDirectory

from dateutil.tz import tzutc
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension
from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr import stac
from stactools.noaa_cdr.cdr import OceanHeatContent
from tests import test_data


def test_create_collection() -> None:
    collection = stac.create_collection(OceanHeatContent)
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
        items = stac.create_items(OceanHeatContent, temporary_directory, [path])
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
            assert asset.common_metadata.created
            assert asset.common_metadata.updated

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
        items = stac.create_items(OceanHeatContent, temporary_directory, paths)
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
        items = stac.create_items(OceanHeatContent, temporary_directory, paths)
    assert len(items) == 80
    for item in items:
        assert len(item.assets) == 1
        item.validate()


def test_create_items_one_netcdf_latest_only() -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    with TemporaryDirectory() as temporary_directory:
        items = stac.create_items(
            OceanHeatContent, temporary_directory, [path], latest_only=True
        )
    assert len(items) == 1
    items[0].validate()

import datetime
from tempfile import TemporaryDirectory

from dateutil.tz import tzutc

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

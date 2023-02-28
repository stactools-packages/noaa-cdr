import datetime
from pathlib import Path

from dateutil.tz import tzutc
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension

import stactools.noaa_cdr.stac
from stactools.noaa_cdr.sea_surface_temperature_optimum_interpolation import stac
from tests import test_data


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.extent.temporal.intervals == [
        [datetime.datetime(1981, 9, 1, tzinfo=tzutc()), None]
    ]
    RasterExtension.validate_has_extension(collection, add_if_missing=False)
    collection.set_self_href("")
    collection.validate()


def test_create_item() -> None:
    path = test_data.get_external_data("oisst-avhrr-v02r01.20220913.nc")
    item = stac.create_item(path)
    assert item.id == "oisst-avhrr-v02r01.20220913"
    assert item.datetime is None
    assert item.common_metadata.start_datetime == datetime.datetime(
        2022, 9, 13, 0, 0, 0, tzinfo=tzutc()
    )
    assert item.common_metadata.end_datetime == datetime.datetime(
        2022, 9, 13, 23, 59, 59, tzinfo=tzutc()
    )
    assert item.bbox == [-180.0, -90.0, 180.0, 90.0]
    assert (
        "https://stac-extensions.github.io/processing/v1.1.0/schema.json"
        in item.stac_extensions
    )
    assert item.properties["processing:level"] == "L4"
    assert len(item.assets) == 1
    asset = item.assets["netcdf"]
    assert asset.href == path
    assert asset.media_type == "application/netcdf"
    assert asset.roles
    assert set(asset.roles) == {"data"}
    assert asset.common_metadata.created == datetime.datetime(
        2022, 9, 28, 9, 14, 0, tzinfo=tzutc()
    )
    assert asset.common_metadata.updated == datetime.datetime(
        2022, 9, 28, 9, 14, 0, tzinfo=tzutc()
    )

    projection = ProjectionExtension.ext(item)
    assert projection.epsg == 4326
    assert projection.shape == [720, 1440]
    assert projection.transform == [0.25, 0.0, -180, 0.0, -0.25, 90.0]

    item.validate()


def test_add_items(tmp_path: Path) -> None:
    path = test_data.get_external_data("oisst-avhrr-v02r01.20220913.nc")
    item = stac.create_item(path)
    item = stactools.noaa_cdr.stac.add_cogs(item, str(tmp_path))
    assert len(item.assets) == 5
    asset = item.assets["sst"]
    assert asset.href == str(tmp_path / "oisst-avhrr-v02r01.20220913-sst.tif")
    asset = item.assets["anom"]
    assert asset.href == str(tmp_path / "oisst-avhrr-v02r01.20220913-anom.tif")
    asset = item.assets["err"]
    assert asset.href == str(tmp_path / "oisst-avhrr-v02r01.20220913-err.tif")
    asset = item.assets["ice"]
    assert asset.href == str(tmp_path / "oisst-avhrr-v02r01.20220913-ice.tif")
    item.validate()

from stactools.noaa_cdr import stac
from stactools.noaa_cdr.constants import Cdr


def test_create_collection() -> None:
    collection = stac.create_collection(Cdr.OceanHeatContent)
    assert collection.id == "noaa-cdr-ocean-heat-content"
    assert len(collection.assets) == 44
    for asset in collection.assets.values():
        assert asset.title is not None
        assert asset.description is not None
        assert asset.media_type == "application/netcdf"
        assert asset.roles == ["data"]

    collection.set_self_href("")
    collection.validate_all()

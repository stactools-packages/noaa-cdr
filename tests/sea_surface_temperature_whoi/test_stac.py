from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr.sea_surface_temperature_whoi import stac

from .. import test_data


def test_create_item() -> None:
    path = test_data.get_external_data(
        "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
    )
    item = stac.create_item(path)
    item.validate()


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.id == "noaa-cdr-sea-surface-temperature-whoi"

    scientific = ScientificExtension.ext(collection)
    assert scientific.doi == "10.7289/V5FB510W"
    assert scientific.citation

    collection.set_self_href("")
    collection.validate()

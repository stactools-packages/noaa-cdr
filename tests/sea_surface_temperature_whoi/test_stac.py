from pathlib import Path

from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr.sea_surface_temperature_whoi import stac

from .. import test_data


def test_create_cog_items(tmp_path: Path) -> None:
    path = test_data.get_external_data(
        "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
    )
    items = stac.create_cog_items(path, str(tmp_path))
    assert len(items) == 8
    for i, item in enumerate(items):
        assert item.id == f"SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223-{i}"
        assert item.bbox == [-180, -90, 180, 90]
        assert item.datetime is None
        assert len(item.assets) == 2
        assert "fill_missing_qc" in item.assets
        assert "sea_surface_temperature" in item.assets
        item.validate()


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.id == "noaa-cdr-sea-surface-temperature-whoi"

    scientific = ScientificExtension.ext(collection)
    assert scientific.doi == "10.7289/V5FB510W"
    assert scientific.citation

    collection.set_self_href("")
    collection.validate()

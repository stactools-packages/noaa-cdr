from pathlib import Path

import pytest
from pystac.extensions.scientific import ScientificExtension

from stactools.noaa_cdr import cog
from stactools.noaa_cdr.sea_surface_temperature_whoi import stac

from .. import test_data


def test_create_item() -> None:
    path = test_data.get_external_data(
        "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
    )
    item = stac.create_item(path)

    assert item.bbox == [-180, -90, 180, 90]

    item.validate()


@pytest.mark.xfail
def test_cogify(tmp_path: Path) -> None:
    path = test_data.get_external_data(
        "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
    )
    assets = cog.cogify(path, str(tmp_path))
    assert len(assets) == 8


def test_create_collection() -> None:
    collection = stac.create_collection()
    assert collection.id == "noaa-cdr-sea-surface-temperature-whoi"

    scientific = ScientificExtension.ext(collection)
    assert scientific.doi == "10.7289/V5FB510W"
    assert scientific.citation

    collection.set_self_href("")
    collection.validate()

from pathlib import Path

import pytest
from pystac import Collection, Item

from tests import run_command, test_data


def test_create_collection(tmp_path: Path) -> None:
    destination = tmp_path / "collection.json"
    result = run_command(
        "noaa-cdr sea-surface-temperature-optimum-interpolation "
        f"create-collection {destination}"
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    paths = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(paths) == 1
    collection = Collection.from_file(str(destination))
    assert collection.id == "noaa-cdr-sea-surface-temperature-optimum-interpolation"
    collection.validate()


@pytest.mark.external_data
def test_create_item(tmp_path: Path) -> None:
    destination = tmp_path / "item.json"
    infile = test_data.get_external_data("oisst-avhrr-v02r01.20220913.nc")
    result = run_command(
        "noaa-cdr sea-surface-temperature-optimum-interpolation "
        f"create-item {infile} {destination}"
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    paths = [p for p in tmp_path.iterdir() if p.suffix == ".json"]
    assert len(paths) == 1
    item = Item.from_file(str(tmp_path / paths[0]))
    item.validate()


@pytest.mark.external_data
def test_create_item_with_cogs(tmp_path: Path) -> None:
    path = test_data.get_external_data("oisst-avhrr-v02r01.20220913.nc")
    result = run_command(
        "noaa-cdr sea-surface-temperature-optimum-interpolation "
        f"create-item --cogs {path} {tmp_path}/out.json"
    )
    assert result.exit_code == 0

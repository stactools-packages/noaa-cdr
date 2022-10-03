import os.path
from pathlib import Path

from pystac import Collection, ItemCollection

from tests import run_command, test_data


def test_create_collection(tmp_path: Path) -> None:
    destination = os.path.join(tmp_path, "collection.json")
    result = run_command(f"noaa-cdr ocean-heat-content create-collection {destination}")
    assert result.exit_code == 0, "\n{}".format(result.output)
    paths = [p for p in os.listdir(tmp_path) if p.endswith(".json")]
    assert len(paths) == 1
    collection = Collection.from_file(destination)
    assert collection.id == "noaa-cdr-ocean-heat-content"
    collection.validate()


def test_create_items(tmp_path: Path) -> None:
    destination = os.path.join(tmp_path, "item-collection.json")
    infile = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    result = run_command(
        f"noaa-cdr ocean-heat-content create-items {infile} {destination}"
    )
    assert result.exit_code == 0, "\n{}".format(result.output)

    paths = [p for p in os.listdir(tmp_path) if p.endswith(".json")]
    assert len(paths) == 1

    item_collection = ItemCollection.from_file(os.path.join(tmp_path, paths[0]))
    assert len(item_collection) == 17
    for item in item_collection:
        item.validate()


def test_download() -> None:
    result = run_command("noaa-cdr ocean-heat-content download --help")
    assert result.exit_code == 0


def test_cogify(tmp_path: Path) -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    result = run_command(f"noaa-cdr ocean-heat-content cogify {path} -o {tmp_path}")
    assert result.exit_code == 0

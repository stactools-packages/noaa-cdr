from pathlib import Path

from pystac import Collection, ItemCollection

from .. import run_command, test_data


def test_create_cog_items(tmp_path: Path) -> None:
    path = test_data.get_external_data(
        "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
    )
    result = run_command(
        f"noaa-cdr sea-surface-temperature-whoi create-cog-items {path} {tmp_path}/out.json"
    )
    assert result.exit_code == 0, result.output
    item_collection = ItemCollection.from_file(str(tmp_path / "out.json"))
    for item in item_collection:
        item.validate()


def test_create_collection(tmp_path: Path) -> None:
    result = run_command(
        f"noaa-cdr sea-surface-temperature-whoi create-collection {tmp_path}/out.json"
    )
    assert result.exit_code == 0, result.output
    collection = Collection.from_file(str(tmp_path / "out.json"))
    collection.validate()

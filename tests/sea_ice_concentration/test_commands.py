from pathlib import Path

from pystac import Collection, Item

from .. import run_command, test_data


def test_create_item(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    result = run_command(
        f"noaa-cdr sea-ice-concentration create-item {path} {tmp_path}/out.json"
    )
    assert result.exit_code == 0, result.output
    item = Item.from_file(str(tmp_path / "out.json"))
    item.validate()


def test_create_item_with_cogs(tmp_path: Path) -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    result = run_command(
        f"noaa-cdr sea-ice-concentration create-item --cogs {path} {tmp_path}/out.json"
    )
    assert result.exit_code == 0, result.output
    item = Item.from_file(str(tmp_path / "out.json"))
    item.validate()


def test_create_collection(tmp_path: Path) -> None:
    result = run_command(
        f"noaa-cdr sea-ice-concentration create-collection {tmp_path}/out.json"
    )
    assert result.exit_code == 0, result.output
    collection = Collection.from_file(str(tmp_path / "out.json"))
    collection.validate()

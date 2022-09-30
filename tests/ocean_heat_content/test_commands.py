import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

from click import Command, Group
from pystac import Collection, ItemCollection
from stactools.testing.cli_test import CliTestCase

from stactools.noaa_cdr.commands import create_noaa_cdr_command
from tests import test_data


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_noaa_cdr_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            destination = os.path.join(temporary_directory, "collection.json")
            result = self.run_command(
                f"noaa-cdr ocean-heat-content create-collection {destination}"
            )
            assert result.exit_code == 0, "\n{}".format(result.output)
            paths = [p for p in os.listdir(temporary_directory) if p.endswith(".json")]
            assert len(paths) == 1
            collection = Collection.from_file(destination)
            assert collection.id == "noaa-cdr-ocean-heat-content"
            collection.validate()

    def test_create_items(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            destination = os.path.join(temporary_directory, "item-collection.json")
            infile = test_data.get_external_data(
                "heat_content_anomaly_0-2000_yearly.nc"
            )
            result = self.run_command(
                f"noaa-cdr ocean-heat-content create-items {infile} {destination}"
            )
            assert result.exit_code == 0, "\n{}".format(result.output)

            paths = [p for p in os.listdir(temporary_directory) if p.endswith(".json")]
            assert len(paths) == 1

            item_collection = ItemCollection.from_file(
                os.path.join(temporary_directory, paths[0])
            )
            assert len(item_collection) == 17
            for item in item_collection:
                item.validate()

    def test_download(self) -> None:
        result = self.run_command("noaa-cdr ocean-heat-content download --help")
        assert result.exit_code == 0

    def test_cogify(self) -> None:
        path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
        with TemporaryDirectory() as temporary_directory:
            result = self.run_command(
                f"noaa-cdr ocean-heat-content cogify {path} -o {temporary_directory}"
            )
            assert result.exit_code == 0

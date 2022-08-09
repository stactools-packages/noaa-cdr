import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

import pystac
from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.noaa_cdr.commands import create_noaa_cdr_command
from stactools.noaa_cdr.constants import Names


class CommandsTest(CliTestCase):
    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_noaa_cdr_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-collection command and validate

            # Example:
            destination = os.path.join(tmp_dir, "collection.json")

            result = self.run_command(f"noaa-cdr create-collection {destination}")

            assert result.exit_code == 0, "\n{}".format(result.output)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            assert len(jsons) == 1

            collection = pystac.read_file(destination)
            assert collection.id == "my-collection-id"
            # assert collection.other_attr...

            collection.validate()

    def test_create_item(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            # Run your custom create-item command and validate

            # Example:
            infile = "/path/to/asset.tif"
            destination = os.path.join(tmp_dir, "item.json")
            result = self.run_command(f"noaa-cdr create-item {infile} {destination}")
            assert result.exit_code == 0, "\n{}".format(result.output)

            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            assert len(jsons) == 1

            item = pystac.read_file(destination)
            assert item.id == "my-item-id"
            # assert item.other_attr...

            item.validate()

    def test_download(self) -> None:
        result = self.run_command("noaa-cdr download --help")
        assert result.exit_code == 0

    def test_list(self) -> None:
        result = self.run_command("noaa-cdr list")
        assert result.exit_code == 0
        assert result.stdout.strip() == "\n".join(Names)

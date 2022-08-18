import os.path
from tempfile import TemporaryDirectory
from typing import Callable, List

import pystac
import pytest
from click import Command, Group
from stactools.testing.cli_test import CliTestCase

from stactools.noaa_cdr import Cdr
from stactools.noaa_cdr.commands import create_noaa_cdr_command


@pytest.mark.usefixtures("external_data")
class CommandsTest(CliTestCase):
    netcdf_path_for_cogify: str

    def create_subcommand_functions(self) -> List[Callable[[Group], Command]]:
        return [create_noaa_cdr_command]

    def test_create_collection(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            destination = os.path.join(tmp_dir, "collection.json")
            result = self.run_command(
                f"noaa-cdr create-collection ocean-heat-content {destination}"
            )
            assert result.exit_code == 0, "\n{}".format(result.output)
            jsons = [p for p in os.listdir(tmp_dir) if p.endswith(".json")]
            assert len(jsons) == 1
            collection = pystac.read_file(destination)
            assert collection.id == "noaa-cdr-ocean-heat-content"
            collection.validate()

    @pytest.mark.xfail
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
        assert result.stdout.strip() == "\n".join(Cdr.slugs())

    def test_cogify(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            result = self.run_command(
                f"noaa-cdr cogify {self.netcdf_path_for_cogify} -o {temporary_directory}"
            )
            assert result.exit_code == 0

import os.path
from typing import Any, Dict, Sequence, Union

import click
from click.testing import CliRunner, Result
from stactools.noaa_cdr import ocean_heat_content
from stactools.noaa_cdr.commands import create_noaa_cdr_command
from stactools.testing.test_data import TestData

external_data: Dict[str, Any] = {
    "oisst-avhrr-v02r01.20220913.nc": {
        "url": (
            "https://www.ncei.noaa.gov/data/"
            "sea-surface-temperature-optimum-interpolation/v2.1/"
            "access/avhrr/202209/oisst-avhrr-v02r01.20220913.nc"
        )
    },
    "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc": {
        "url": (
            "https://www.ncei.noaa.gov/data/"
            "sea-surface-temperature-whoi/access/2021/"
            "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
        )
    },
}

for href in ocean_heat_content.iter_noaa_hrefs():
    external_data[os.path.basename(href)] = {"url": href}


test_data = TestData(__file__, external_data)


@click.group()
def test_cli() -> None:
    pass


create_noaa_cdr_command(test_cli)


def run_command(command: Union[str, Sequence[str]]) -> Result:
    runner = CliRunner()
    result = runner.invoke(test_cli, command, catch_exceptions=False)
    if result.output:
        print(result.output)
    return result

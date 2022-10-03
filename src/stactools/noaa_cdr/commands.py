import logging

import click_logging
from click import Command, Group

from .ocean_heat_content.commands import (
    create_command as create_ocean_heat_content_command,
)
from .sea_ice_concentration.commands import (
    create_command as create_sea_ice_concentration_command,
)
from .sea_surface_temperature_optimum_interpolation.commands import (
    create_command as create_sea_surface_temperature_optimum_interpolation_command,
)
from .sea_surface_temperature_whoi.commands import (
    create_command as create_sea_surface_temperature_whoi_command,
)

logger = logging.getLogger(__name__)
click_logging.basic_config(logger)


def create_noaa_cdr_command(cli: Group) -> Command:
    """Creates the stactools-noaa-cdr command line utility."""

    @cli.group(
        "noaa-cdr",
        short_help=("Commands for working with NOAA Climate Data Records (CDR)"),
    )
    @click_logging.simple_verbosity_option(logger)  # type: ignore
    def noaa_cdr() -> None:
        pass

    create_ocean_heat_content_command(noaa_cdr)
    create_sea_ice_concentration_command(noaa_cdr)
    create_sea_surface_temperature_optimum_interpolation_command(noaa_cdr)
    create_sea_surface_temperature_whoi_command(noaa_cdr)

    return noaa_cdr

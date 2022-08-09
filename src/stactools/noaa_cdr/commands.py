import logging

import click
from click import Command, Group

from stactools.noaa_cdr import stac
from stactools.noaa_cdr.constants import Names

logger = logging.getLogger(__name__)


def create_noaa_cdr_command(cli: Group) -> Command:
    """Creates the stactools-noaa-cdr command line utility."""

    @cli.group(
        "noaa-cdr",
        short_help=("Commands for working with NOAA Climate Data Records (CDR)"),
    )
    def noaa_cdr() -> None:
        pass

    @noaa_cdr.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    def create_collection_command(destination: str) -> None:
        """Creates a STAC Collection

        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_collection()

        collection.set_self_href(destination)

        collection.save_object()

        return None

    @noaa_cdr.command("create-item", short_help="Create a STAC item")
    @click.argument("source")
    @click.argument("destination")
    def create_item_command(source: str, destination: str) -> None:
        """Creates a STAC Item

        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        item = stac.create_item(source)

        item.save_object(dest_href=destination)

        return None

    @noaa_cdr.command("download", short_help="Download data from NOAA's HTTP server")
    @click.argument("name")
    @click.argument("destination")
    def create_download_command(name: str, destination: str) -> None:
        """Downloads data from NOAA's HTTP server.

        Args:
            name (str): The name of the CDR. Use `stac noaa-cdr list` to print
                a list of available CDRs.
            destination (str): The directory in which to store the CDR data.
        """
        raise NotImplementedError

    @noaa_cdr.command("list", short_help="List the names of all supported CDRs")
    def create_list_command() -> None:
        """Prints the names of all supported CDRs."""
        for name in Names:
            print(name.value)

    return noaa_cdr

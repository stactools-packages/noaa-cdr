import os

import click
import pystac.utils
from click import Command, Group

import stactools.noaa_cdr.stac
from stactools.noaa_cdr.sea_ice_concentration import stac


def create_command(noaa_cdr: Group) -> Command:
    @noaa_cdr.group(
        "sea-ice-concentration",
        short_help=("Commands for working with the Sea Ice Concentration CDR "),
    )
    def sea_ice_concentration() -> None:
        pass

    @sea_ice_concentration.command(
        "create-item", short_help="Create a STAC item from a NetCDF"
    )
    @click.argument("source")
    @click.argument("destination")
    @click.option(
        "--cogs/--no-cogs",
        help="Create COGs for this NetCDF file next to the item",
        default=False,
        show_default=True,
    )
    def create_item(source: str, destination: str, cogs: bool) -> None:
        item = stac.create_item(source)
        if cogs:
            directory = os.path.dirname(destination)
            os.makedirs(directory, exist_ok=True)
            stactools.noaa_cdr.stac.add_cogs(item, directory)
        for key, asset in item.assets.items():
            asset.href = pystac.utils.make_relative_href(asset.href, destination)
            item.assets[key] = asset
        item.save_object(include_self_link=False, dest_href=destination)

    @sea_ice_concentration.command(
        "create-collection", short_help="Create a STAC collection"
    )
    @click.argument("destination")
    def create_collection_command(destination: str) -> None:
        """Creates a STAC Collection.

        \b
        Args:
            destination (str): The destination file.
        """
        collection = stac.create_collection()
        collection.set_self_href(destination)
        collection.save()

    return sea_ice_concentration

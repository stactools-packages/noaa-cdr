from pathlib import Path

import click
import pystac.utils
from click import Command, Group
from pystac import ItemCollection

from stactools.noaa_cdr.sea_surface_temperature_whoi import stac


def create_command(noaa_cdr: Group) -> Command:
    @noaa_cdr.group(
        "sea-surface-temperature-whoi",
        short_help=("Commands for working with the Sea Surface Temperature - WHOI CDR"),
    )
    def sea_surface_temperature_whoi() -> None:
        pass

    @sea_surface_temperature_whoi.command(
        "create-items", short_help="Create a STAC item collection from a NetCDF"
    )
    @click.argument("source")
    @click.argument("destination")
    def create_items(source: str, destination: str) -> None:
        items = stac.create_items(source, str(Path(destination).parent))
        for item in items:
            for key, asset in item.assets.items():
                asset.href = pystac.utils.make_relative_href(asset.href, destination)
                item.assets[key] = asset
        item_collection = ItemCollection(items)
        item_collection.save_object(dest_href=destination)

    @sea_surface_temperature_whoi.command(
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

    return sea_surface_temperature_whoi

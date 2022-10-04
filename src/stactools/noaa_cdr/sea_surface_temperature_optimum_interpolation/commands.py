import os

import click
import pystac.utils
from click import Command, Group
from pystac import CatalogType

import stactools.noaa_cdr.stac

from . import stac


def create_command(noaa_cdr: Group) -> Command:
    @noaa_cdr.group(
        "sea-surface-temperature-optimum-interpolation",
        short_help=(
            "Commands for working with the Sea Surface Temperature "
            "- Optimum Interpolation CDR"
        ),
    )
    def sea_surface_temperature_optimum_interpolation() -> None:
        pass

    @sea_surface_temperature_optimum_interpolation.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    def create_collection(
        destination: str,
    ) -> None:
        """Creates a STAC Collection.

        \b
        Args:
            destination (str): An HREF for the Collection JSON
        """
        collection = stac.create_collection(catalog_type=CatalogType.SELF_CONTAINED)
        collection.set_self_href(destination)
        collection.save()
        return None

    @sea_surface_temperature_optimum_interpolation.command(
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

    return sea_surface_temperature_optimum_interpolation

import os

import click
import pystac.utils
from click import Command, Group, Path
from pystac import CatalogType, Item

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
    def create_collection_command(
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
    def create_item_command(source: str, destination: str) -> None:
        """Creates a STAC Item from the provided NetCDF.

        \b
        Args:
            source (str): HREF of the Asset associated with the Item.
            destination (str): The destination file.
        """
        item = stac.create_item(source)
        for key, asset in item.assets.items():
            asset.href = pystac.utils.make_relative_href(asset.href, destination)
            item.assets[key] = asset
        item.save_object(include_self_link=False, dest_href=destination)

    @sea_surface_temperature_optimum_interpolation.command(
        "add-cogs",
        short_help="Create a Cloud-Optimized GeoTIFF (COG) from a CDR NetCDF file",
    )
    @click.argument("infile", type=Path(exists=True))
    def add_cogs_command(infile: str) -> None:
        item = Item.from_file(infile)
        item = stactools.noaa_cdr.stac.add_cogs(
            item,
            os.path.dirname(infile),
        )
        item.save_object(include_self_link=False)

    return sea_surface_temperature_optimum_interpolation

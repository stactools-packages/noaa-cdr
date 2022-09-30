import os
from typing import Optional

import click
import pystac.utils
from click import Command, Group, Path
from pystac import CatalogType

from .. import cog
from . import stac
from .constants import PROFILE


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
    @click.option(
        "-c",
        "--cogify",
        is_flag=True,
        show_default=True,
        help="Cogify the netcdf",
        default=False,
    )
    @click.option(
        "-d", "--cog-directory", help="The directory in which to store the COGs"
    )
    def create_item_command(
        source: str, destination: str, cogify: bool, cog_directory: Optional[str]
    ) -> None:
        """Creates a STAC Item from the provided NetCDF.

        \b
        Args:
            source (str): HREF of the Asset associated with the Item.
            destination (str): The destination file.
            cog_directory (str): The folder that will hold the COGs. If not
                provided, the COGs will be stored in the same directory as the item
                collection.
        """
        if not cog_directory:
            cog_directory = os.path.dirname(destination)
        os.makedirs(cog_directory, exist_ok=True)
        item = stac.create_item(source, cogify, cog_directory)
        for key, asset in item.assets.items():
            asset.href = pystac.utils.make_relative_href(asset.href, destination)
            item.assets[key] = asset
        item.save_object(include_self_link=False, dest_href=destination)

    @sea_surface_temperature_optimum_interpolation.command(
        "cogify",
        short_help="Create a Cloud-Optimized GeoTIFF (COG) from a CDR NetCDF file",
    )
    @click.argument("infile", type=Path(exists=True))
    @click.option("-o", "--outdir", help="The output directory")
    def cogify_command(infile: str, outdir: Optional[Path]) -> None:
        """Creates a Cloud-Optimized GeoTIFF (COG) from a CDR NetCDF file.

        The COG will have the same file name but with a .tif extension.

        \b
        Args:
            infile (str): The input NetCDF file.
            outdir (click.Path, optional): The output directory. If not
                provided, the tif will be created in the same directory as the
                NetCDF.
        """
        if outdir:
            directory = str(outdir)
        else:
            directory = None
        assets = cog.cogify(infile, PROFILE, directory)
        print(f"Wrote {len(assets)} COGs to {directory}")

    return sea_surface_temperature_optimum_interpolation

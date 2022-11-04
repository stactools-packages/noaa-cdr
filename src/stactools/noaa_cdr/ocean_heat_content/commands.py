import os.path
from tempfile import TemporaryDirectory
from typing import List, Optional

import click
import pystac.utils
import requests
import stactools.core.copy
import tqdm
from click import Command, Group, Path
from pystac import CatalogType, ItemCollection

from . import cog, stac


def create_command(noaa_cdr: Group) -> Command:
    @noaa_cdr.group(
        "ocean-heat-content",
        short_help=("Commands for working with the Ocean Heat Content CDR"),
    )
    def ocean_heat_content() -> None:
        pass

    @ocean_heat_content.command(
        "create-collection",
        short_help="Creates a STAC collection",
    )
    @click.argument("destination")
    @click.option(
        "-c",
        "--create-items",
        is_flag=True,
        default=False,
        show_default=True,
        help="Create items and include them with this collection",
    )
    @click.option(
        "-l",
        "--latest-only",
        is_flag=True,
        default=False,
        show_default=True,
        help="Only create the most recent items (only used if --create-items is True)",
    )
    @click.option(
        "-d",
        "--local-directory",
        help="Read NetCDFs from this local directory instead of from NOAA's HTTP "
        "servers (only used if --create-items is True)",
    )
    def create_collection_command(
        destination: str,
        create_items: bool,
        latest_only: bool,
        local_directory: Optional[str],
    ) -> None:
        """Creates a STAC Collection for the Ocean Heat Content CDR.

        \b
        Args:
            destination (str): An HREF for the Collection JSON
            create_items (bool): Create items and include them in this
                collection. Defaults to False.
            latest_only (bool): Only create the most recent items, not all. Only
                used if --create-items is true. Defaults to False.
            local_directory (Optional[str]): Read netcdf files from this local
                directory instead of from NOAA's servers. Only used if
                --create-items is true.
        """
        if create_items:
            with TemporaryDirectory() as temporary_directory:
                collection = stac.create_collection(
                    catalog_type=CatalogType.SELF_CONTAINED,
                    cog_directory=temporary_directory,
                    latest_only=latest_only,
                    local_directory=local_directory,
                )
                collection.normalize_hrefs(os.path.dirname(destination))
                stactools.core.copy.move_all_assets(
                    collection,
                    make_hrefs_relative=True,
                    copy=False,
                    ignore_conflicts=True,
                )
        else:
            collection = stac.create_collection(catalog_type=CatalogType.SELF_CONTAINED)
        collection.set_self_href(destination)
        collection.save()
        return None

    @ocean_heat_content.command(
        "create-items", short_help="Create STAC items from a NetCDF"
    )
    @click.argument("source", nargs=-1)
    @click.argument("destination", nargs=1)
    @click.option(
        "-c", "--cog-directory", help="The directory in which to store the COGs"
    )
    def create_items_command(
        source: List[str], destination: str, cog_directory: Optional[str]
    ) -> None:
        """Creates a STAC ItemCollection for the provided NetCDFs.

        \b
        Args:
            source (str): HREF of the Asset associated with the Item.
            destination (str): The destination file that will hold the item collection.
            cog_directory (str): The folder that will hold the COGs. If not
                provided, the COGs will be stored in the same directory as the item
                collection.
        """
        if not cog_directory:
            cog_directory = os.path.dirname(destination)
        os.makedirs(cog_directory, exist_ok=True)
        items = stac.create_items(source, cog_directory)
        for item in items:
            for key, asset in item.assets.items():
                asset.href = pystac.utils.make_relative_href(asset.href, destination)
                item.assets[key] = asset
        item_collection = ItemCollection(items)
        item_collection.save_object(destination)

    @ocean_heat_content.command(
        "download", short_help="Download data from NOAA's HTTP server"
    )
    @click.argument("destination")
    def download_command(destination: str) -> None:
        """Downloads data from NOAA's HTTP server.

        \b
        Args:
            name (str): The name of the CDR. Use `stac noaa-cdr list` to print
                a list of available CDRs.
            destination (str): The directory in which to store the CDR data.
        """
        os.makedirs(destination, exist_ok=True)
        for href in stactools.noaa_cdr.ocean_heat_content.iter_noaa_hrefs():
            path = os.path.join(destination, os.path.basename(href))
            if os.path.exists(path):
                print(f"File already downloaded, skipping: {path}")
            response = requests.get(href, stream=True)
            with tqdm.wrapattr(
                open(path, "wb"),
                "write",
                miniters=1,
                desc=href.split("/")[-1],
                total=int(response.headers.get("content-length", 0)),
            ) as fout:
                for chunk in response.iter_content(chunk_size=4096):
                    fout.write(chunk)

    @ocean_heat_content.command(
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
            os.makedirs(str(outdir), exist_ok=True)
        cogs = cog.cogify(infile, None if outdir is None else str(outdir))
        print(f"Wrote {len(cogs)} COGs to {os.path.dirname(cogs[0].asset().href)}")

    return ocean_heat_content

import logging
import os
from typing import List, Optional

import click
import pystac.utils
import requests
from click import Command, Group, Path
from pystac import ItemCollection
from tqdm import tqdm

import stactools.noaa_cdr
from stactools.noaa_cdr import stac
from stactools.noaa_cdr.cdr import Cdr

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
    @click.argument("cdr-name")
    @click.argument("destination")
    @click.option(
        "-s",
        "--include-self-link",
        is_flag=True,
        default=False,
        show_default=True,
        help="Include a self link in the collection",
    )
    def create_collection_command(
        cdr_name: str, destination: str, include_self_link: bool
    ) -> None:
        """Creates a STAC Collection

        \b
        Args:
            cdr_name (str): The name of a CDR. Use `stac noaa-cdr list` to see a
                list of available names.
            destination (str): An HREF for the Collection JSON
        """
        cdr = Cdr.from_slug(cdr_name)
        collection = stac.create_collection(cdr)
        collection.set_self_href(destination)
        collection.save_object(include_self_link=include_self_link)
        return None

    @noaa_cdr.command("create-items", short_help="Create STAC items from a NetCDF")
    @click.argument("name")
    @click.argument("source", nargs=-1)
    @click.argument("destination", nargs=1)
    @click.option(
        "-c", "--cog-directory", help="The directory in which to store the COGs"
    )
    def create_item_command(
        name: str, source: List[str], destination: str, cog_directory: Optional[str]
    ) -> None:
        """Creates a STAC ItemCollection for the provided NetCDFs.

        \b
        Args:
            name (str): The CDR name.
            source (str): HREF of the Asset associated with the Item.
            destination (str): The destination file that will hold the item collection.
            cog_directory (str): The folder that will hold the COGs. If not
                provided, the COGs will be stored in the same directory as the item
                collection.
        """
        cdr = Cdr.from_slug(name)
        if not cog_directory:
            cog_directory = os.path.dirname(destination)
        os.makedirs(cog_directory, exist_ok=True)
        items = stac.create_items(cdr, cog_directory, source)
        for item in items:
            for key, asset in item.assets.items():
                asset.href = pystac.utils.make_relative_href(asset.href, destination)
                item.assets[key] = asset
        item_collection = ItemCollection(items)
        item_collection.save_object(destination)

    @noaa_cdr.command("download", short_help="Download data from NOAA's HTTP server")
    @click.argument("name")
    @click.argument("destination")
    def create_download_command(name: str, destination: str) -> None:
        """Downloads data from NOAA's HTTP server.

        \b
        Args:
            name (str): The name of the CDR. Use `stac noaa-cdr list` to print
                a list of available CDRs.
            destination (str): The directory in which to store the CDR data.
        """
        cdr = Cdr.from_slug(name)
        os.makedirs(destination, exist_ok=True)
        for href in cdr.hrefs():
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

    @noaa_cdr.command("list", short_help="List the names of all supported CDRs")
    def create_list_command() -> None:
        """Prints the names of all supported CDRs."""
        for slug in Cdr.slugs():
            print(slug)

    @noaa_cdr.command(
        "cogify",
        short_help="Create a Cloud-Optimized GeoTIFF (COG) from a CDR NetCDF file",
    )
    @click.argument("infile", type=Path(exists=True))
    @click.option("-o", "--outdir", help="The output directory")
    def create_cog_command(infile: str, outdir: Optional[Path]) -> None:
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
        cogs = stactools.noaa_cdr.cogify(
            infile, None if outdir is None else str(outdir)
        )
        print(f"Wrote {len(cogs)} COGs to {os.path.dirname(cogs[0].path)}")

    return noaa_cdr

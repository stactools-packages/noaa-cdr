import logging
import os
from typing import Optional

import click
import requests
from click import ClickException, Command, Group, Path
from tqdm import tqdm

import stactools.noaa_cdr
from stactools.noaa_cdr import constants, stac
from stactools.noaa_cdr.constants import Cdr

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
        cdr = Cdr.from_value(cdr_name)
        collection = stac.create_collection(cdr)
        collection.set_self_href(destination)
        collection.save_object(include_self_link=include_self_link)
        return None

    @noaa_cdr.command("create-item", short_help="Create a STAC item")
    @click.argument("source")
    @click.argument("destination")
    def create_item_command(source: str, destination: str) -> None:
        """Creates a STAC Item

        \b
        Args:
            source (str): HREF of the Asset associated with the Item
            destination (str): An HREF for the STAC Item
        """
        raise NotImplementedError

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
        resolved_name = next((n for n in Cdr if n == name), None)
        if not resolved_name:
            print("Run `stac noaa-cdr list` to see all supported names")
            raise ClickException(f"invalid name: {name}")
        os.makedirs(destination, exist_ok=True)
        for href in constants.hrefs(resolved_name):
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
        for cdr in Cdr:
            print(cdr.value)

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
        paths = stactools.noaa_cdr.cogify(
            infile, None if outdir is None else str(outdir)
        )
        print(f"Wrote {len(paths)} COGs to {os.path.dirname(paths[0])}")

    return noaa_cdr

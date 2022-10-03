import click
from click import Command, Group

from stactools.noaa_cdr.sea_surface_temperature_whoi import stac


def create_command(noaa_cdr: Group) -> Command:
    @noaa_cdr.group(
        "sea-surface-temperature-whoi",
        short_help=("Commands for working with the Sea Surface Temperature - WHOI CDR"),
    )
    def sea_surface_temperature_whoi() -> None:
        pass

    @sea_surface_temperature_whoi.command(
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
        item.save_object(include_self_link=False, dest_href=destination)

    return sea_surface_temperature_whoi

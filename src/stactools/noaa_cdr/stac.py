import os.path
from typing import List, Type

from pystac import Asset, CatalogType, Collection, Item

from .cdr import Cdr
from .cogify import cogify
from .constants import LICENSE, PROVIDERS

DEFAULT_CATALOG_TYPE = CatalogType.SELF_CONTAINED


def create_collection(
    cdr: Type[Cdr], catalog_type: CatalogType = DEFAULT_CATALOG_TYPE
) -> Collection:
    """Creates a STAC Collection for the provided CDR.

    Args:
        cdr (Cdr): The CDR.
        catalog_type (CatalogType): The type of catalog to create.

    Returns:
        Collection: STAC Collection object
    """

    collection = Collection(
        id=f"noaa-cdr-{cdr.slug()}",
        title=cdr.title(),
        description=cdr.description(),
        license=LICENSE,
        providers=PROVIDERS,
        extent=cdr.extent(),
        catalog_type=catalog_type,
    )
    for href in cdr.hrefs():
        key = os.path.splitext(os.path.basename(href))[0]
        collection.add_asset(
            key,
            Asset(
                href=href,
                title=cdr.asset_title(key),
                description=cdr.asset_description(key),
                media_type="application/netcdf",
                roles=["data"],
            ),
        )

    return collection


def create_items(
    cdr: Type[Cdr],
    cog_directory: str,
    hrefs: List[str] = [],
    latest_only: bool = False,
) -> List[Item]:
    """Creates COG items for the provided CDR.

    Args:
        cdr (Type[Cdr]): The CDR type.
        cog_directory (str): Directory in which to store the COGs.
        hrefs (List[str], optional): The NetCDF hrefs to use to create the
            items. Defaults to [], which means COGs will be created for all NOAA
            HTTP hrefs defined for this CDR.
        latest_only (bool): Only create STAC items for the latest data. Useful
            for creating a small subset of a CDRs items. Defaults to false.

    Returns:
        List[Item]: A list of PySTAC items.
    """
    if not hrefs:
        hrefs = list(cdr.hrefs())
    items: List[Item] = []
    for href in hrefs:
        cogs = cogify(href, cog_directory, latest_only)
        items = cdr.update_items(items, cogs)
    return items

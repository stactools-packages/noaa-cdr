import os.path
from typing import Type

from pystac import Asset, CatalogType, Collection

from .cdr import Cdr
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

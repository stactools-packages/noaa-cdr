import os.path

from pystac import Asset, CatalogType, Collection

from . import constants, utils
from .constants import LICENSE, PROVIDERS, Cdr

DEFAULT_CATALOG_TYPE = CatalogType.SELF_CONTAINED


def create_collection(
    cdr: Cdr, catalog_type: CatalogType = DEFAULT_CATALOG_TYPE
) -> Collection:
    """Creates a STAC Collection for the provided CDR.

    Args:
        cdr (Cdr): The CDR.
    Returns:
        Collection: STAC Collection object
    """

    collection = Collection(
        id=f"noaa-cdr-{cdr.value}",
        title=cdr.title,
        description=cdr.description,
        license=LICENSE,
        providers=PROVIDERS,
        extent=cdr.extent,
        catalog_type=catalog_type,
    )
    for href in constants.hrefs(cdr):
        key = os.path.splitext(os.path.basename(href))[0]
        collection.add_asset(key, Asset(href=href, title=utils.asset_key_to_title(key)))

    return collection

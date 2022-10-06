from pystac import CatalogType, Collection, Item

from .. import stac
from ..constants import DEFAULT_CATALOG_TYPE, LICENSE, PROVIDERS
from .constants import DESCRIPTION, EXTENT, ID, TITLE


def create_collection(catalog_type: CatalogType = DEFAULT_CATALOG_TYPE) -> Collection:
    return Collection(
        id=ID,
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=catalog_type,
        license=LICENSE,
        keywords=[],
        providers=PROVIDERS,
    )


def create_item(href: str) -> Item:
    return stac.create_item(href)

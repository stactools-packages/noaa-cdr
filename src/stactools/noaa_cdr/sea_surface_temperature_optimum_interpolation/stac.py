from typing import Optional

from pystac import CatalogType, Collection, Item

from .. import cog, stac
from ..constants import DEFAULT_CATALOG_TYPE, LICENSE, PROVIDERS
from .constants import DESCRIPTION, EXTENT, ID, PROFILE, TITLE


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


def create_item(
    href: str, cogify: bool = False, cog_directory: Optional[str] = None
) -> Item:
    item = stac.create_item(href, remap_longitudes=True)
    if cogify:
        assets = cog.cogify(href, PROFILE, cog_directory)
        for key, value in assets.items():
            item.add_asset(key, value)

    return item

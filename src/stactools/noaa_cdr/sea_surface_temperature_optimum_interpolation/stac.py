from pystac import CatalogType, Collection, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.scientific import ScientificExtension

from .. import stac
from ..constants import DEFAULT_CATALOG_TYPE, LICENSE, PROVIDERS
from .constants import (
    CITATION,
    DESCRIPTION,
    DOI,
    EXTENT,
    HOMEPAGE_LINK,
    ID,
    ITEM_ASSETS,
    KEYWORDS,
    LICENSE_LINK,
    TITLE,
)


def create_collection(catalog_type: CatalogType = DEFAULT_CATALOG_TYPE) -> Collection:
    collection = Collection(
        id=ID,
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=catalog_type,
        license=LICENSE,
        keywords=KEYWORDS,
        providers=PROVIDERS,
    )

    collection.add_link(LICENSE_LINK)
    collection.add_link(HOMEPAGE_LINK)

    item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
    item_assets.item_assets = dict(
        (k, AssetDefinition(v)) for (k, v) in ITEM_ASSETS.items()
    )

    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = DOI
    scientific.citation = CITATION

    return collection


def create_item(href: str) -> Item:
    return stac.create_item(href)

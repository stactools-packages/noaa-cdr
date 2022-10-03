from pystac import Collection, Item
from pystac.extensions.scientific import ScientificExtension

from .. import stac
from ..constants import DEFAULT_CATALOG_TYPE
from .constants import CITATION, DESCRIPTION, DOI, EXTENT, ID, TITLE


def create_item(href: str) -> Item:
    return stac.create_item(href)


def create_collection() -> Collection:
    collection = Collection(
        id=ID,
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=DEFAULT_CATALOG_TYPE,
    )

    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = DOI
    scientific.citation = CITATION

    return collection

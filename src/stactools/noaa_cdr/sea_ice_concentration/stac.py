import os.path

from pystac import Collection, Item
from pystac.extensions.scientific import ScientificExtension

from .. import stac
from ..constants import (
    CLASSIFICATION_EXTENSION_SCHEMA,
    DEFAULT_CATALOG_TYPE,
    NETCDF_ASSET_KEY,
)
from . import cog
from .constants import CITATION, DESCRIPTION, DOI, EXTENT, TITLE


def create_item(href: str) -> Item:
    # We have to manually override the id because the `id` attribute in the
    # netcdf is set to the DOI.
    return stac.create_item(href, id=os.path.splitext(os.path.basename(href))[0])


def add_cogs(item: Item, directory: str) -> Item:
    netcdf_asset = item.assets[NETCDF_ASSET_KEY]
    assets = cog.cogify(netcdf_asset.href, directory)
    for key, asset in assets.items():
        item.add_asset(key, asset)
    item.stac_extensions.append(CLASSIFICATION_EXTENSION_SCHEMA)
    return item


def create_collection() -> Collection:
    collection = Collection(
        id="noaa-cdr-sea-ice-concentration",
        description=DESCRIPTION,
        extent=EXTENT,
        title=TITLE,
        catalog_type=DEFAULT_CATALOG_TYPE,
    )

    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = DOI
    scientific.citation = CITATION

    return collection

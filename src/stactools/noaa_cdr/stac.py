import logging
import os.path
from typing import List, Optional, Type

from pystac import Asset, CatalogType, Collection, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.scientific import ScientificExtension

from .cdr import Cdr
from .cogify import cogify
from .constants import LICENSE, PROVIDERS

DEFAULT_CATALOG_TYPE = CatalogType.SELF_CONTAINED

logger = logging.getLogger(__name__)


def create_collection(
    cdr: Type[Cdr],
    catalog_type: CatalogType = DEFAULT_CATALOG_TYPE,
    cog_directory: Optional[str] = None,
    latest_only: bool = False,
    local_directory: Optional[str] = None,
) -> Collection:
    """Creates a STAC Collection for the provided CDR.

    Args:
        cdr (Cdr): The CDR.
        catalog_type (CatalogType): The type of catalog to create.
        cog_directory (Optional[str]): If provided, COGs will be created in this
            directory, and items pointing to those COGs will be added to the
            collection.
        latest_only (bool): Only create the most recent items, not all. Only
            used if cog_directory is not None. Defaults to False.
        local_directory (Optional[str]): Read netcdf files from this local
            directory instead of from NOAA's servers. Only used if
            cog_directory is not None.

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
    collection.add_link(cdr.license_link())
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
    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = cdr.doi()
    scientific.citation = cdr.citation()
    if cog_directory:
        hrefs = []
        if local_directory:
            hrefs = list(cdr.local_hrefs(local_directory))
        items = create_items(cdr, cog_directory, hrefs=hrefs, latest_only=latest_only)
        asset_definitions = dict()
        for item in items:
            for key, asset in item.assets.items():
                if key not in asset_definitions:
                    if asset.title:
                        # TODO this pattern may not work for all CDRs
                        title = asset.title.split(" : ")[0]
                    else:
                        title = None
                    asset_definitions[key] = AssetDefinition.create(
                        title=title,
                        description=asset.description,
                        media_type=asset.media_type,
                        roles=asset.roles,
                    )
        collection.add_items(items)
        collection.update_extent_from_items()
        item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
        item_assets.item_assets = asset_definitions

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
    for i, href in enumerate(hrefs):
        logger.info(f"Creating COGs for {href} ({i + 1} / {len(hrefs)})")
        cogs = cogify(href, cog_directory, latest_only)
        items = cdr.update_items(items, cogs)
    return items

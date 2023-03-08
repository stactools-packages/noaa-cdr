import logging
import os.path
from typing import Iterator, List, Optional

import pystac.utils
from pystac import Asset, CatalogType, Collection, Item
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import RasterExtension
from pystac.extensions.scientific import ScientificExtension
from stactools.core.io import ReadHrefModifier

from ..constants import (
    DEFAULT_CATALOG_TYPE,
    GLOBAL_BBOX,
    GLOBAL_GEOMETRY,
    INTERVAL_ATTRIBUTE_NAME,
    LICENSE,
    MAX_DEPTH_ATTRIBUTE_NAME,
    PROVIDERS,
)
from . import cog, iter_noaa_hrefs
from .cog import Cog
from .constants import (
    ASSET_METADATA,
    CITATION,
    DESCRIPTION,
    DOI,
    EPSG,
    EXTENT,
    HOMEPAGE_LINK,
    ID,
    KEYWORDS,
    LICENSE_LINK,
    TITLE,
    TRANSFORM,
)

logger = logging.getLogger(__name__)


def create_collection(
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
        id=ID,
        title=TITLE,
        description=DESCRIPTION,
        license=LICENSE,
        providers=PROVIDERS,
        extent=EXTENT,
        catalog_type=catalog_type,
        keywords=KEYWORDS,
    )
    collection.add_link(LICENSE_LINK)
    collection.add_link(HOMEPAGE_LINK)
    for href in iter_noaa_hrefs():
        key = os.path.splitext(os.path.basename(href))[0]
        collection.add_asset(
            key,
            Asset(
                href=href,
                title=ASSET_METADATA[key]["title"],
                description=ASSET_METADATA[key]["description"],
                media_type="application/netcdf",
                roles=["data", "source"],
            ),
        )
    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = DOI
    scientific.citation = CITATION
    has_raster_extension = False
    if cog_directory:
        hrefs = []
        if local_directory:
            hrefs = list(_local_hrefs(local_directory))
        items = create_items(hrefs, cog_directory, latest_only=latest_only)
        asset_definitions = dict()
        for item in items:
            for key, asset in item.assets.items():
                if key not in asset_definitions:
                    if asset.title:
                        title = asset.title.split(" : ")[0]
                    else:
                        title = None
                    asset_definition = AssetDefinition.create(
                        title=title,
                        description=asset.description,
                        media_type=asset.media_type,
                        roles=asset.roles,
                    )
                    try:
                        raster = RasterExtension.ext(asset)
                    except ValueError:
                        pass
                    else:
                        has_raster_extension = True
                        if raster.bands:
                            asset_definition.properties["raster:bands"] = [
                                band.to_dict() for band in raster.bands
                            ]
                    asset_definitions[key] = asset_definition

        if has_raster_extension:
            RasterExtension.add_to(collection)

        collection.add_items(items)
        collection.update_extent_from_items()
        item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
        item_assets.item_assets = asset_definitions

    return collection


def create_items(
    hrefs: List[str],
    directory: str,
    cog_hrefs: Optional[List[str]] = None,
    latest_only: bool = False,
    read_href_modifier: Optional[ReadHrefModifier] = None,
) -> List[Item]:
    """Creates items from the netcdf files located at hrefs.

    If HREFs is an empty list, all NOAA hrefs (see `iter_noaa_hrefs`) will be used.
    """

    if not hrefs:
        hrefs = list(iter_noaa_hrefs())
    items: List[Item] = []
    for i, href in enumerate(hrefs):
        logger.info(f"Creating COGs for {href} ({i + 1} / {len(hrefs)})")
        cogs = cog.cogify(
            href,
            directory,
            cog_hrefs=cog_hrefs,
            latest_only=latest_only,
            read_href_modifier=read_href_modifier,
        )
        items = _update_items(items, cogs)
    return items


def _update_items(items: List[Item], cogs: List[Cog]) -> List[Item]:
    items_as_dict = dict((item.id, item) for item in items)
    for c in cogs:
        id = c.item_id()
        if id not in items_as_dict:
            item = Item(
                id=id,
                geometry=GLOBAL_GEOMETRY,
                bbox=GLOBAL_BBOX,
                datetime=None,
                properties={
                    "start_datetime": pystac.utils.datetime_to_str(c.start_datetime),
                    "end_datetime": pystac.utils.datetime_to_str(c.end_datetime),
                    INTERVAL_ATTRIBUTE_NAME: c.interval(),
                    MAX_DEPTH_ATTRIBUTE_NAME: c.max_depth(),
                },
            )
            projection = ProjectionExtension.ext(item, add_if_missing=True)
            projection.epsg = EPSG
            projection.shape = c.profile.shape
            projection.transform = list(TRANSFORM)[0:6]
            items_as_dict[id] = item
        item = items_as_dict[id]
        title = c.attributes["title"].split(" : ")[0]
        min_depth = int(c.attributes["geospatial_vertical_min"])
        max_depth = int(c.attributes["geospatial_vertical_max"])
        asset = c.asset()
        asset.title = f"{title} : {min_depth}-{max_depth}m {c.time_interval_as_str()}"
        item.add_asset(c.asset_key(), asset)
        # The asset has the raster extension, but we need to make sure the item
        # has the schema url.
        _ = RasterExtension.ext(asset, add_if_missing=True)
        items_as_dict[id] = item
    return list(items_as_dict.values())


def _local_hrefs(directory: str) -> Iterator[str]:
    for href in iter_noaa_hrefs():
        yield os.path.join(directory, os.path.basename(href))

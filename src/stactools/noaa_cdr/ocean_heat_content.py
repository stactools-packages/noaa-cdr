import copy
import datetime
import importlib
import json
import logging
import os.path
from dataclasses import dataclass
from typing import Any, Dict, Hashable, Iterator, List, Optional

import fsspec
import numpy
import pystac.utils
import shapely.geometry
import xarray
from pystac import (
    Asset,
    CatalogType,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    Provider,
    ProviderRole,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import DataType, RasterExtension
from pystac.extensions.scientific import ScientificExtension
from rasterio import Affine

from stactools.noaa_cdr.profile import Profile

from . import dataset, time
from .time import TimeResolution

logger = logging.getLogger(__name__)

ID = "noaa-cdr-ocean-heat-content"
TITLE = "Global Ocean Heat Content CDR"
DESCRIPTION = (
    "The Ocean Heat Content Climate Data Record (CDR) is a set "
    "of ocean heat content anomaly (OHCA) time-series for 1955-present "
    "on 3-monthly, yearly, and pentadal (five-yearly) scales. This CDR "
    "quantifies ocean heat content change over time, which is an "
    "essential metric for understanding climate change and the Earth's "
    "energy budget. It provides time-series for multiple depth ranges in "
    "the global ocean and each of the major basins (Atlantic, Pacific, "
    "and Indian) divided by hemisphere (Northern, Southern)."
)
BBOX = [-180.0, -90.0, 180.0, 90.0]
GEOMETRY = shapely.geometry.mapping(shapely.geometry.box(*BBOX))
SPATIAL_EXTENT = SpatialExtent(bboxes=BBOX)
TEMPORAL_EXTENT = TemporalExtent(intervals=[[datetime.datetime(1955, 1, 1), None]])
EXTENT = Extent(SPATIAL_EXTENT, TEMPORAL_EXTENT)
PROVIDERS = [
    Provider(
        name="National Centers for Environmental Information",
        description="NCEI is the Nation's leading authority for environmental data, and manage "
        "one of the largest archives of atmospheric, coastal, geophysical, and "
        "oceanic research in the world. NCEI contributes to the NESDIS mission "
        "by developing new products and services that span the science disciplines "
        "and enable better data discovery.",
        roles=[
            ProviderRole.PRODUCER,
            ProviderRole.PROCESSOR,
            ProviderRole.LICENSOR,
            ProviderRole.HOST,
        ],
        url="https://www.ncei.noaa.gov/",
    )
]
LICENSE = "proprietary"
BASE_TIME = datetime.datetime(1955, 1, 1)
DEFAULT_CATALOG_TYPE = CatalogType.SELF_CONTAINED
LICENSE_LINK = Link(
    rel="license",
    target="https://www.ncei.noaa.gov/pub/data/sds/cdr/CDRs/"
    "Ocean_Heat_Content/UseAgreement_01B-41.pdf",
    media_type=MediaType.PDF,
    title="NOAA CDR Ocean Heat Content Use Agreement",
)
ASSET_METADATA = json.loads(
    importlib.resources.read_text("stactools.noaa_cdr", "ocean-heat-content.json")
)
DOI = "10.7289/v53f4mvp"
CITATION = (
    "Levitus, Sydney; Antonov, John I.; Boyer, Tim P.; Baranova, Olga K.; "
    "García, Hernán E.; Locarnini, Ricardo A.; Mishonov, Alexey V.; Reagan, James R.; "
    "[Seidov, Dan; Yarosh, Evgeney; Zweng, Melissa M. (2017). "
    "NCEI ocean heat content, temperature anomalies, salinity anomalies, thermosteric "
    "sea level anomalies, halosteric sea level anomalies, and total steric sea level "
    "anomalies from 1955 to present calculated from in situ oceanographic subsurface "
    "profile data (NCEI Accession 0164586). [indicate subset used]. "
    "NOAA National Centers for Environmental Information. Dataset. "
    "https://doi.org/10.7289/v53f4mvp. Accessed [date]."
)
GDAL_TRANSFORM = [-180.0, 1.0, 0.0, -90.0, 0.0, 1.0]
PROFILE = Profile(
    width=360,
    height=180,
    data_type=DataType.FLOAT32,
    transform=Affine.from_gdal(*GDAL_TRANSFORM),
    nodata=numpy.nan,
)


@dataclass(frozen=True)
class Cog:
    """Dataclass to hold the result of a cogification operation."""

    asset: Asset
    time_resolution: TimeResolution
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    datetime: datetime.datetime
    attributes: Dict[Hashable, Any]

    def time_interval_as_str(self) -> str:
        """Returns this COG's time interval as a string."""
        return self.time_resolution.as_str(self.datetime)

    def item_id(self) -> str:
        """Returns the item id."""
        depth = int(self.attributes["geospatial_vertical_max"])
        return f"ocean-heat-content-{self.time_interval_as_str()}-{depth}m"

    def asset_key(self) -> str:
        """Returns this COG's asset key."""
        parts = []
        for part in self.attributes["id"].split("_"):
            if part == "anomaly":
                break
            else:
                parts.append(part)
        return "_".join(parts)


def iter_noaa_hrefs() -> Iterator[str]:
    """Iterates over NOAA hrefs for this CDR."""

    for variable in [
        "heat_content",
        "mean_halosteric_sea_level",
        "mean_salinity",
        "mean_temperature",
        "mean_thermosteric_sea_level",
        "mean_total_steric_sea_level",
    ]:
        for depth in ["100", "700", "2000"]:
            for period in ["monthly", "pentad", "seasonal", "yearly"]:
                if period == "monthly" and variable != "heat_content":
                    continue
                elif depth == "100" and variable not in [
                    "mean_salinity",
                    "mean_temperature",
                ]:
                    continue
                yield (
                    "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data/0164586/"
                    f"derived/{variable}_anomaly_0-{depth}_{period}.nc"
                )


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
    )
    collection.add_link(LICENSE_LINK)
    for href in iter_noaa_hrefs():
        key = os.path.splitext(os.path.basename(href))[0]
        collection.add_asset(
            key,
            Asset(
                href=href,
                title=ASSET_METADATA[key]["title"],
                description=ASSET_METADATA[key]["description"],
                media_type="application/netcdf",
                roles=["data"],
            ),
        )
    scientific = ScientificExtension.ext(collection, add_if_missing=True)
    scientific.doi = DOI
    scientific.citation = CITATION
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
                        if raster.bands:
                            asset_definition.properties["raster:bands"] = [
                                band.to_dict() for band in raster.bands
                            ]
                    asset_definitions[key] = asset_definition
        collection.add_items(items)
        collection.update_extent_from_items()
        item_assets = ItemAssetsExtension.ext(collection, add_if_missing=True)
        item_assets.item_assets = asset_definitions

    return collection


def create_items(
    hrefs: List[str], directory: str, latest_only: bool = False
) -> List[Item]:
    """Creates items from the netcdf files located at hrefs.

    If HREFs is an empty list, all NOAA hrefs (see `iter_noaa_hrefs`) will be used.
    """

    if not hrefs:
        hrefs = list(iter_noaa_hrefs())
    items: List[Item] = []
    for i, href in enumerate(hrefs):
        logger.info(f"Creating COGs for {href} ({i + 1} / {len(hrefs)})")
        cogs = cogify(href, directory, latest_only=latest_only)
        items = _update_items(items, cogs)
    return items


def _update_items(items: List[Item], cogs: List[Cog]) -> List[Item]:
    items_as_dict = dict((item.id, item) for item in items)
    for cog in cogs:
        id = cog.item_id()
        if id not in items_as_dict:
            item = Item(
                id=id,
                geometry=GEOMETRY,
                bbox=BBOX,
                datetime=cog.datetime,
                properties={
                    "start_datetime": pystac.utils.datetime_to_str(cog.start_datetime),
                    "end_datetime": pystac.utils.datetime_to_str(cog.end_datetime),
                    "created": pystac.utils.datetime_to_str(datetime.datetime.now()),
                },
            )
            proj = ProjectionExtension.ext(item, add_if_missing=True)
            proj.epsg = PROFILE.epsg
            proj.shape = PROFILE.shape
            proj.transform = GDAL_TRANSFORM
            items_as_dict[id] = item
        item = items_as_dict[id]
        title = cog.attributes["title"].split(" : ")[0]
        min_depth = int(cog.attributes["geospatial_vertical_min"])
        max_depth = int(cog.attributes["geospatial_vertical_max"])
        cog.asset.title = (
            f"{title} : {min_depth}-{max_depth}m {cog.time_interval_as_str()}"
        )
        item.add_asset(cog.asset_key(), cog.asset)
        # The asset has the raster extension, but we need to make sure the item
        # has the schema url.
        _ = RasterExtension.ext(cog.asset, add_if_missing=True)
        items_as_dict[id] = item
    return list(items_as_dict.values())


def cogify(
    href: str, outdir: Optional[str] = None, latest_only: bool = False
) -> List[Cog]:
    if outdir is None:
        outdir = os.path.dirname(href)
    cogs = list()
    with fsspec.open(href) as file:
        with xarray.open_dataset(file, decode_times=False) as ds:
            time_resolution = TimeResolution.from_value(ds.time_coverage_resolution)
            variable = dataset.data_variable_name(ds)
            num_records = len(ds[variable].time)
            for i, month_offset in enumerate(ds[variable].time):
                if latest_only and i < (num_records - 1):
                    continue
                dt = time.add_months_to_datetime(BASE_TIME, month_offset)
                start_datetime, end_datetime = time_resolution.datetime_bounds(dt)
                suffix = time_resolution.as_str(dt)
                path = os.path.join(
                    outdir,
                    f"{os.path.splitext(os.path.basename(href))[0]}_{suffix}.tif",
                )
                values = ds[variable].isel(time=i).values.squeeze()
                profile = copy.deepcopy(PROFILE)
                profile.unit = ds[variable].units.replace("_", " ")
                asset = dataset.write_cog(
                    values,
                    path,
                    profile,
                )
                cogs.append(
                    Cog(
                        asset=asset,
                        time_resolution=time_resolution,
                        datetime=dt,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        attributes=ds.attrs,
                    )
                )
    return cogs


def _local_hrefs(directory: str) -> Iterator[str]:
    for href in iter_noaa_hrefs():
        yield os.path.join(directory, os.path.basename(href))

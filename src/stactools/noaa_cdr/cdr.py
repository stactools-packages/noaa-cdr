import datetime
import math
import os.path
from abc import ABC, abstractmethod
from typing import Iterable, List, Type, Union, cast

import dateutil.parser
import pystac.utils
from pystac import Asset, Extent, Item, MediaType, TemporalExtent
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import NoDataStrings, RasterBand, RasterExtension

from .cogify import Cog
from .constants import BBOX, COLLECTION_ASSET_METADATA, GEOMETRY, SPATIAL_EXTENT


class Cdr(ABC):
    """Abstract base class for all supported CDRs."""

    @classmethod
    def from_slug(cls, slug: str) -> Type["Cdr"]:
        """Returns the CDR class with the given slug.

        Raises:
            ValueError: Raised if the slug does not resolve to a CDR class.

        Returns:
            Type[Cdr]: A subclass of Cdr.
        """
        for subclass in cls.__subclasses__():
            if subclass.slug() == slug:
                return subclass
        raise ValueError(f"Unknown CDR slug: {slug}")

    @staticmethod
    @abstractmethod
    def slug() -> str:
        """Returns a short, descriptive string for this CDR.

        Should be slug-case.

        Returns:
            str: The slug
        """
        ...

    @classmethod
    def slugs(cls) -> Iterable[str]:
        """Iterates over all registered CDR slugs.

        Yields:
            str: A Cdr subclass's slug.
        """
        for cdr in cls.cdrs():
            yield cdr.slug()

    @classmethod
    def cdrs(cls) -> Iterable[Type["Cdr"]]:
        """Iterates over all defined CDRs.

        Yields:
            Type[Cdr]: A Cdr subclass
        """
        for subclass in cls.__subclasses__():
            yield subclass

    @staticmethod
    @abstractmethod
    def title() -> str:
        """Returns the collection title for this CDR.

        Returns:
            str: The title.
        """
        ...

    @staticmethod
    @abstractmethod
    def description() -> str:
        """Returns the collection description for this CDR.

        Returns:
            str: The description.
        """
        ...

    @classmethod
    def extent(cls) -> Extent:
        """Returns this CDR's temporal and spatial extent.

        Returns:
            Extent: The spatiotemporal extent of the CDR.
        """
        return Extent(SPATIAL_EXTENT, cls.temporal_extent())

    @staticmethod
    @abstractmethod
    def temporal_extent() -> TemporalExtent:
        """Returns this CDR's temporal extent.

        Returns:
            TemporalExtent: The temporal extent.
        """
        ...

    @classmethod
    def asset_title(cls, key: str) -> str:
        """Returns an asset's title for this Cdr and asset key.

        Args:
            key (str): The asset key.

        Returns:
            str: The asset title.
        """
        # Cast is appropriate because we know the structure of the metadata json file.
        return cast(str, COLLECTION_ASSET_METADATA[cls.slug()][key]["title"])

    @classmethod
    def asset_description(cls, key: str) -> str:
        """Returns an asset's deescription for this Cdr and asset key.

        Args:
            key (str): The asset key.

        Returns:
            str: The asset description.
        """
        # Cast is appropriate because we know the structure of the metadata json file.
        return cast(str, COLLECTION_ASSET_METADATA[cls.slug()][key]["description"])

    @staticmethod
    @abstractmethod
    def hrefs() -> Iterable[str]:
        """Iterates over a list of hrefs of this CDR's NetCDF assets."""
        ...

    @classmethod
    def local_hrefs(cls, directory: str) -> Iterable[str]:
        """Iterates over this CDR's hrefs, but each href is rebased to live in
        the provided directory.

        Used for pre-fetched NetCDFs."""
        for href in cls.hrefs():
            yield os.path.join(directory, os.path.basename(href))

    @classmethod
    def update_items(cls, items: List[Item], cogs: List[Cog]) -> List[Item]:
        """Updates a list of items with new COGs.

        Args:
            items (List[Item]): STAC Items to be updated w/ new COGs.
            cogs (List[Cog]): A list of Cog objects.

        Returns:
            List[Item]: STAC Items, updated with the COGs.
        """
        items_as_dict = dict((item.id, item) for item in items)
        for cog in cogs:
            id = cls.item_id(cog)
            if id not in items_as_dict:
                item = Item(
                    id=id,
                    geometry=GEOMETRY,
                    bbox=BBOX,
                    datetime=cog.datetime,
                    properties={
                        "start_datetime": pystac.utils.datetime_to_str(
                            cog.start_datetime
                        ),
                        "end_datetime": pystac.utils.datetime_to_str(cog.end_datetime),
                        "created": pystac.utils.datetime_to_str(
                            datetime.datetime.now()
                        ),
                    },
                )
                proj = ProjectionExtension.ext(item, add_if_missing=True)
                proj.epsg = cog.epsg
                proj.shape = cog.shape
                proj.transform = cog.transform
                items_as_dict[id] = item
            item = items_as_dict[id]
            title = f"{cog.attributes['title']} {cog.time_interval_as_str()}"
            asset = Asset(
                href=cog.path, title=title, media_type=MediaType.COG, roles=["data"]
            )
            asset.common_metadata.created = dateutil.parser.parse(
                cog.attributes["date_created"]
            )
            asset.common_metadata.updated = dateutil.parser.parse(
                cog.attributes["date_modified"]
            )
            item.add_asset(cls.asset_key(cog), asset)
            raster = RasterExtension.ext(asset, add_if_missing=True)
            if math.isnan(cog.nodata):
                nodata: Union[NoDataStrings, float] = NoDataStrings.NAN
            else:
                nodata = cog.nodata
            raster.bands = [
                RasterBand.create(nodata=nodata, data_type=cog.data_type, unit=cog.unit)
            ]
            items_as_dict[id] = item
        return list(items_as_dict.values())

    @classmethod
    @abstractmethod
    def item_id(cls, cog: Cog) -> str:
        """Creates an Item id from a COG.

        Args:
            cog (Cog): A Cog.

        Returns:
            str: The Item id.
        """
        ...

    @staticmethod
    @abstractmethod
    def asset_key(cog: Cog) -> str:
        """Returns the asset key for the given COG.

        Args:
            cog (Cog): A Cog.

        Returns:
            str: The asset key.
        """
        ...


class OceanHeatContent(Cdr):
    """The ocean heat content CDR.

    https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content
    """

    @staticmethod
    def slug() -> str:
        return "ocean-heat-content"

    @staticmethod
    def title() -> str:
        return "Global Ocean Heat Content CDR"

    @staticmethod
    def description() -> str:
        return (
            "The Ocean Heat Content Climate Data Record (CDR) is a set "
            "of ocean heat content anomaly (OHCA) time-series for 1955-present "
            "on 3-monthly, yearly, and pentadal (five-yearly) scales. This CDR "
            "quantifies ocean heat content change over time, which is an "
            "essential metric for understanding climate change and the Earth's "
            "energy budget. It provides time-series for multiple depth ranges in "
            "the global ocean and each of the major basins (Atlantic, Pacific, "
            "and Indian) divided by hemisphere (Northern, Southern)."
        )

    @staticmethod
    def temporal_extent() -> TemporalExtent:
        return TemporalExtent(intervals=[[datetime.datetime(1955, 1, 1), None]])

    @staticmethod
    def hrefs() -> Iterable[str]:
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

    @classmethod
    def item_id(cls, cog: Cog) -> str:
        time_interval_as_str = cog.time_interval_as_str()
        depth = int(cog.attributes["geospatial_vertical_max"])
        return f"{cls.slug()}-{time_interval_as_str}-{depth}m"

    @staticmethod
    def asset_key(cog: Cog) -> str:
        parts = []
        for part in cog.attributes["id"].split("_"):
            if part == "anomaly":
                break
            else:
                parts.append(part)
        return "_".join(parts)

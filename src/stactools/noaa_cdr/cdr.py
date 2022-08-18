import datetime
from abc import ABC, abstractmethod
from typing import Iterable, Type, cast

from pystac import Extent, TemporalExtent

from .constants import COLLECTION_ASSET_METADATA, SPATIAL_EXTENT


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

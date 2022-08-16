import datetime
from enum import Enum, unique
from typing import List

from pystac import Extent, Provider, ProviderRole, SpatialExtent, TemporalExtent

SPATIAL_EXTENT = SpatialExtent(bboxes=[-180.0, -90.0, 180.0, 90.0])
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


@unique
class Cdr(str, Enum):
    # https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content
    OceanHeatContent = "ocean-heat-content"

    @classmethod
    def from_value(cls, value: str) -> "Cdr":
        """Finds the Cdr that matches the provided value.

        Args:
            value (str): The name of the CDR.

        Returns:
            Cdr: The resolved Cdr.

        Raises:
            ValueError: Raised if the value is not a valid CDR name.
        """
        cdr = next(
            (c for c in Cdr if c.value == value),
            None,
        )
        if cdr is None:
            raise ValueError("Encountered unexpected CDR name: " f"{value}")
        else:
            return cdr

    @property
    def title(self) -> str:
        """Returns the Collection title for this CDR.

        Returns:
            str: The CDR title.
        """
        if self == Cdr.OceanHeatContent:
            return "Global Ocean Heat Content CDR"
        else:
            raise NotImplementedError

    @property
    def description(self) -> str:
        """Returns the Collection description for this CDR.

        Returns:
            str: The CDR description.
        """
        if self == Cdr.OceanHeatContent:
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
        else:
            raise NotImplementedError

    @property
    def extent(self) -> Extent:
        """Returns this CDR's temporal and spatial extent.

        Returns:
            Extent: The spatiotemporal extent of the CDR.
        """
        return Extent(SPATIAL_EXTENT, self.temporal_extent)

    @property
    def temporal_extent(self) -> TemporalExtent:
        """Returns this CDR's temporal.

        Returns:
            TemporalExtent: The temporal extent of the CDR.
        """
        if self == Cdr.OceanHeatContent:
            return TemporalExtent(intervals=[[datetime.datetime(1955, 1, 1), None]])
        else:
            raise NotImplementedError


@unique
class TimeResolution(str, Enum):
    """Used to parse ``time_coverage_resolution`` in NetCDF files.

    We _could_ use a real datetime package, e.g. pandas's Timedelta, but since
    we only need to handle four cases, this simple structure seemed easier.
    """

    Monthly = "P01M"
    Seasonal = "P03M"
    Yearly = "P01Y"
    Pentadal = "P05Y"

    @classmethod
    def from_value(cls, value: str) -> "TimeResolution":
        """Finds the TimeResolution that matches the provided value.

        Args:
            value (str): The string value of the TimeResolution, per NetCDF standard.

        Returns:
            TimeResolution: The resolved time resolution.

        Raises:
            ValueError: Raised if the value is not a valid TimeResolution.
        """
        time_resolution = next(
            (t for t in TimeResolution if t.value == value),
            None,
        )
        if time_resolution is None:
            raise ValueError(
                "Encountered unexpected time_coverage_resolution: " f"{value}"
            )
        else:
            return time_resolution


def hrefs(name: Cdr) -> List[str]:
    """Returns all asset hrefs for the given CDR name.

    Args:
        name (str): The CDR Name.

    Returns:
        List[str]: The CDR hrefs.
    """
    hrefs = []
    if name == Cdr.OceanHeatContent:
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
                    hrefs.append(
                        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data/0164586/"
                        f"derived/{variable}_anomaly_0-{depth}_{period}.nc"
                    )
    return hrefs

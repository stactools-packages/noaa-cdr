import importlib.resources
import json
from enum import Enum, unique

import shapely.geometry
from pystac import Provider, ProviderRole, SpatialExtent

BBOX = [-180.0, -90.0, 180.0, 90.0]
GEOMETRY = shapely.geometry.mapping(shapely.geometry.box(*BBOX))
SPATIAL_EXTENT = SpatialExtent(bboxes=BBOX)
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
COLLECTION_ASSET_METADATA = json.loads(
    importlib.resources.read_text(
        "stactools.noaa_cdr", "collection-asset-metadata.json"
    )
)


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

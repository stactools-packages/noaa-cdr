import datetime

import importlib_resources
import orjson
from dateutil.tz import tzutc
from pystac import (
    Extent,
    Link,
    MediaType,
    Provider,
    ProviderRole,
    SpatialExtent,
    TemporalExtent,
)

from ..constants import COMMON_KEYWORDS

ID = "noaa-cdr-sea-ice-concentration"
TITLE = "Sea Ice Concentration CDR"
DESCRIPTION = (
    "The Sea Ice Concentration Climate Data "
    "Record (CDR) provides a consistent daily and "
    "monthly time series of sea ice concentrations "
    "for both the north and south Polar Regions "
    "on a 25 km x 25 km grid. These data can be used to "
    "estimate how much of the ocean surface is covered by "
    "ice, and monitor changes in sea ice concentration. The CDR "
    "combines concentration estimates using two algorithms "
    "developed at the NASA Goddard Space Flight Center (GSFC). "
    "Gridded brightness temperatures acquired from Defense "
    "Meteorological Satellite Program (DMSP) passive microwave "
    "radiometers, and, beginning 1 January 2025, the JAXA AMSR2 "
    "sensor, provide the necessary input to produce the dataset."
)
EXTENT = Extent(
    spatial=SpatialExtent(
        [[-180.0, -90, 180, 90], [-180, 31.10, 180.0, 90], [-180, -90, 180.0, -39.36]]
    ),
    temporal=TemporalExtent([[datetime.datetime(1978, 10, 25, tzinfo=tzutc()), None]]),
)
DOI = "10.7265/b18j-z797"
CITATION = (
    "Meier, W. N., F. Fetterer, A. K. Windnagel, J. S. Stewart, "
    "and T. Stafford. 2026. NOAA/NSIDC Climate Data Record of "
    "Passive Microwave Sea Ice Concentration, Version 6. "
    "[Indicate subset used]. Boulder, Colorado USA. NSIDC: National "
    "Snow and Ice Data Center https://doi.org/10.7265/b18j-z797. "
)
PROVIDERS = [
    Provider(
        "National Snow and Ice Data Center",
        (
            "The National Snow and Ice Data Center (NSIDC) at the "
            "University of Colorado Boulder (CU Boulder), part "
            "of the CU Boulder Cooperative Institute for Research "
            "in Environmental Sciences (CIRES), conducts "
            "innovative research and provides open data to "
            "understand how the frozen parts of Earth affect the "
            "rest of the planet and impact society."
        ),
        [
            ProviderRole.PRODUCER,
            ProviderRole.PROCESSOR,
            ProviderRole.LICENSOR,
            ProviderRole.HOST,
        ],
        "https://nsidc.org/data/g02202/versions/6",
    )
]
KEYWORDS = COMMON_KEYWORDS + [
    "Sea ice",
    "Polar",
    "Earth Science",
    "Cryosphere",
    "Sea ice concentration",
]
KEYWORDS.remove("Global")
ITEM_ASSETS = orjson.loads(
    importlib_resources.files("stactools.noaa_cdr.sea_ice_concentration")
    .joinpath("item-assets.json")
    .read_text()
)
HOMEPAGE_LINK = Link(
    rel="about",
    target="https://www.ncei.noaa.gov/products/climate-data-records/sea-ice-concentration",
    media_type=MediaType.HTML,
    title="Sea Ice Concentration CDR",
)
# Want to include this because the user guide will always be findable here.
DATA_HOMEPAGE_LINK = Link(
    target=("https://nsidc.org/data/g02202/versions/6"),
    rel="about",
    media_type=MediaType.HTML,
    title="CDR Homepage",
)
SPATIAL_RESOLUTION = 25000.0

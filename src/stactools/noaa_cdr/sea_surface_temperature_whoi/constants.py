import datetime

import importlib_resources
import orjson
from dateutil.tz import tzutc
from pystac import Extent, Link, MediaType, SpatialExtent, TemporalExtent

from ..constants import COMMON_KEYWORDS

ID = "noaa-cdr-sea-surface-temperature-whoi"
TITLE = "Sea Surface Temperature - WHOI CDR"
DESCRIPTION = (
    "The Sea Surface Temperature-Woods Hole Oceanographic "
    "Institution (WHOI) Climate Data Record (CDR) is one of "
    "three CDRs which combine to form the NOAA Ocean Surface "
    "Bundle (OSB) CDR. The resultant sea surface temperature "
    "(SST) data are produced through modeling the diurnal "
    "variability in combination with AVHRR SST observations. "
    "The final record is output to a 3-hourly 0.25° resolution "
    "grid over the global ice-free oceans from January 1988—present."
)
EXTENT = Extent(
    spatial=SpatialExtent([[-180.0, -90, 180, 90]]),
    temporal=TemporalExtent(
        [[datetime.datetime(1988, 1, 1, tzinfo=tzutc()), None]],
    ),
)
DOI = "10.7289/V5FB510W"
CITATION = (
    "Clayson, Carol Anne; Brown, Jeremiah; and NOAA CDR "
    "Program (2016). NOAA Climate Data Record (CDR) of Sea Surface "
    "Temperature - WHOI, Version 2. NOAA "
    "National Climatic Data Center. doi:10.7289/V5FB510W"
)

LICENSE_LINK = Link(
    "license",
    (
        "https://www.ncei.noaa.gov/pub/data/sds/cdr/CDRs/"
        "Sea%20Surface%20Temperature%20-%20WHOI/UseAgreement_01B-27a.pdf"
    ),
    MediaType.PDF,
    "NOAA CDR Sea Surface Temperature - WHOI Use Agreement",
)

KEYWORDS = COMMON_KEYWORDS + ["Ocean", "Temperature"]

ITEM_ASSETS = orjson.loads(
    importlib_resources.files("stactools.noaa_cdr.sea_surface_temperature_whoi")
    .joinpath("item-assets.json")
    .read_text()
)
HOMEPAGE_LINK = Link(
    rel="about",
    target="https://www.ncei.noaa.gov/products/climate-data-records/sea-surface-temperature-whoi",
    media_type=MediaType.HTML,
    title="Sea Surface Temperature - WHOI CDR",
)

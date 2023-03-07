import datetime

import importlib_resources
import orjson
from dateutil.tz import tzutc
from pystac import Extent, Link, MediaType, TemporalExtent

from ..constants import COMMON_KEYWORDS, GLOBAL_SPATIAL_EXTENT

ID = "noaa-cdr-sea-surface-temperature-optimum-interpolation"
TITLE = "Sea Surface Temperature - Optimum Interpolation CDR"
DESCRIPTION = (
    "The NOAA 1/4° daily Optimum Interpolation Sea Surface "
    "Temperature (or daily OISST) Climate Data Record (CDR) "
    "provides complete ocean temperature fields constructed "
    "by combining bias-adjusted observations from different platforms "
    "(satellites, ships, buoys) on a regular global grid, with gaps "
    "filled in by interpolation. The main input source is satellite "
    "data from the Advanced Very High Resolution Radiometer (AVHRR), "
    "which provides high temporal-spatial coverage from late "
    "1981-present. This input must be adjusted to the buoys due to "
    "erroneous cold SST data following the Mt Pinatubo and El Chichon "
    "eruptions. Applications include climate modeling, resource "
    "management, ecological studies on annual to daily scales."
)
BASE_DATETIME = datetime.datetime(1978, 1, 1, 12, 0, 0, tzinfo=tzutc())
EXTENT = Extent(
    spatial=GLOBAL_SPATIAL_EXTENT,
    temporal=TemporalExtent([[datetime.datetime(1981, 9, 1, tzinfo=tzutc()), None]]),
)
CITATION = (
    "Huang, Boyin; Liu, Chunying; Banzon, Viva F.; Freeman, Eric; Graham, "
    "Garrett; Hankins, Bill; Smith, Thomas M.; Zhang, Huai-Min. (2020): NOAA "
    "0.25-degree Daily Optimum Interpolation Sea Surface Temperature (OISST), Version "
    "2.1. NOAA National Centers for Environmental "
    "Information. https://doi.org/10.25921/RE9P-PT57."
)
DOI = "10.25921/RE9P-PT57"
LICENSE_LINK = Link(
    "license",
    (
        "https://www.ncei.noaa.gov/pub/data/sds/cdr/CDRs/"
        "Sea_Surface_Temperature_Optimum_Interpolation/UseAgreement_01B-09.pdf"
    ),
    MediaType.PDF,
    "NOAA CDR Sea Surface Temperature - Optimum Interpolation Use Agreement",
)

ITEM_ASSETS = orjson.loads(
    importlib_resources.files(
        "stactools.noaa_cdr.sea_surface_temperature_optimum_interpolation"
    )
    .joinpath("item-assets.json")
    .read_text()
)

KEYWORDS = COMMON_KEYWORDS + ["Temperature", "Ocean"]
HOMEPAGE_LINK = Link(
    rel="about",
    target=(
        "https://www.ncei.noaa.gov/products/climate-data-records"
        "/sea-surface-temperature-optimum-interpolation"
    ),
    media_type=MediaType.HTML,
    title="Sea Surface Temperature - Optimum Interpolation CDR",
)

import datetime
import json

import importlib_resources
import pyproj
from dateutil.tz import tzutc
from pystac import Extent, Link, MediaType, TemporalExtent
from rasterio import Affine

from ..constants import COMMON_KEYWORDS, GLOBAL_SPATIAL_EXTENT

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
BASE_TIME = datetime.datetime(1955, 1, 1, tzinfo=tzutc())
TEMPORAL_EXTENT = TemporalExtent(intervals=[[BASE_TIME, None]])
EXTENT = Extent(GLOBAL_SPATIAL_EXTENT, TEMPORAL_EXTENT)
LICENSE_LINK = Link(
    rel="license",
    target="https://www.ncei.noaa.gov/pub/data/sds/cdr/CDRs/"
    "Ocean_Heat_Content/UseAgreement_01B-41.pdf",
    media_type=MediaType.PDF,
    title="NOAA CDR Ocean Heat Content Use Agreement",
)
HOMEPAGE_LINK = Link(
    rel="about",
    target="https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content",
    media_type=MediaType.HTML,
    title="Global Ocean Heat Content CDR",
)
ASSET_METADATA = json.loads(
    importlib_resources.files("stactools.noaa_cdr.ocean_heat_content")
    .joinpath("asset-metadata.json")
    .read_text()
)
DOI = "10.7289/v53f4mvp"
CITATION = (
    "Levitus, Sydney; Antonov, John I.; Boyer, Tim P.; Baranova, Olga K.; "
    "García, Hernán E.; Locarnini, Ricardo A.; Mishonov, Alexey V.; Reagan, James R.; "
    "[Seidov, Dan; Yarosh, Evgeney; Zweng, Melissa M. (2017). "
    "NCEI ocean heat content, temperature anomalies, salinity anomalies, thermosteric "
    "sea level anomalies, halosteric sea level anomalies, and total steric sea level "
    "anomalies from 1955 to present calculated from in situ oceanographic subsurface "
    "profile data (NCEI Accession 0164586)."
    "NOAA National Centers for Environmental Information. Dataset. "
    "https://doi.org/10.7289/v53f4mvp."
)
TRANSFORM = Affine(1.0, 0.0, -180.0, 0.0, -1.0, 90.0)
EPSG = 4326
CRS = pyproj.CRS(f"EPSG:{EPSG}")
KEYWORDS = COMMON_KEYWORDS + ["Temperature", "Ocean"]

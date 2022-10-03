import datetime

from dateutil.tz import tzutc
from pystac import Extent, SpatialExtent, TemporalExtent

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
    "Temperature - WHOI, Version 2. [indicate subset used]. NOAA "
    "National Climatic Data Center. doi:10.7289/V5FB510W [access date]."
)

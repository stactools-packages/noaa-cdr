import datetime

import shapely.geometry
from dateutil.tz import tzutc
from pystac import Extent, TemporalExtent
from pystac.extensions.raster import DataType
from rasterio import Affine

from ..constants import SPATIAL_EXTENT
from ..profile import Profile

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
BBOX = [-180.0, -90.0, 180.0, 90.0]
GEOMETRY = shapely.geometry.mapping(shapely.geometry.box(*BBOX))
PROFILE = Profile(
    width=1440,
    height=720,
    data_type=DataType.INT16,
    transform=Affine(0.25, 0.0, 0.0, 0.0, -0.25, 90.0),
    nodata=-999,
)
EXTENT = Extent(
    spatial=SPATIAL_EXTENT,
    temporal=TemporalExtent([[datetime.datetime(1981, 9, 1, tzinfo=tzutc()), None]]),
)

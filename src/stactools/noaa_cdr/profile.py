import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pystac.extensions.raster import DataType, NoDataStrings, RasterBand
from rasterio import Affine


@dataclass
class Profile:
    width: int
    height: int
    data_type: DataType
    transform: Affine
    nodata: Any
    unit: Optional[str] = None
    scale: Optional[float] = None
    offset: Optional[float] = None
    epsg: int = 4326

    def gtiff(self) -> Dict[str, Any]:
        return {
            "crs": self.crs,
            "width": self.width,
            "height": self.height,
            "dtype": self.data_type,
            "nodata": self.nodata,
            "count": 1,
            "transform": self.transform,
            "driver": "GTiff",
        }

    def raster_band(self) -> RasterBand:
        if math.isnan(self.nodata):
            nodata = NoDataStrings.NAN
        else:
            nodata = self.nodata
        band = RasterBand.create(nodata=nodata, data_type=self.data_type)
        if self.unit:
            band.unit = self.unit
        if self.scale:
            band.scale = self.scale
        if self.offset:
            band.offset = self.offset
        return band

    def cog(self) -> Dict[str, Any]:
        return {"compress": "deflate", "blocksize": 512, "driver": "COG"}

    @property
    def shape(self) -> List[int]:
        return [self.height, self.width]

    @property
    def crs(self) -> str:
        return f"EPSG:{self.epsg}"

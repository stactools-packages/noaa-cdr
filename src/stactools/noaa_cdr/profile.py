import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy
from pyproj import CRS
from pystac.extensions.raster import DataType, NoDataStrings, RasterBand
from rasterio import Affine
from xarray import DataArray


@dataclass
class Profile:
    width: int
    height: int
    data_type: DataType
    transform: Affine
    nodata: Any
    crs: str
    unit: str
    scale: Optional[float]
    offset: Optional[float]

    @classmethod
    def build(
        cls,
        data_array: DataArray,
        crs: CRS,
        transform: Affine,
        nan_nodata: bool = False,
    ) -> "Profile":
        data_type = next(
            (d for d in DataType if d.lower() == str(data_array.dtype)), None
        )
        if not data_type:
            raise ValueError(
                f"No raster extension DataType found for numpy dtype: {data_array.dtype}"
            )
        if nan_nodata:
            nodata: Any = numpy.nan
        else:
            nodata = float(data_array._FillValue)
        if "scale_factor" in data_array.attrs:
            scale = float(data_array.scale_factor)
        else:
            scale = None
        if "add_offset" in data_array.attrs:
            offset = float(data_array.add_offset)
        else:
            offset = None
        return Profile(
            height=data_array.shape[0],
            width=data_array.shape[1],
            data_type=data_type,
            transform=transform,
            nodata=nodata,
            crs=crs,
            scale=scale,
            offset=offset,
            unit=data_array.units.replace("_", " "),
        )

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

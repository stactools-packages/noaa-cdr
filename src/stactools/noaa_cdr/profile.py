import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import numpy
import shapely.geometry
from pyproj import CRS
from pyproj.enums import WktVersion
from pystac.extensions.raster import DataType, NoDataStrings, RasterBand
from rasterio import Affine
from xarray import DataArray, Dataset


@dataclass
class DatasetProfile:
    """Dataset-level profile containing the NetCDF-global attributes."""

    xmin: float
    xmax: float
    ymin: float
    ymax: float
    epsg: Optional[int]
    crs: CRS
    wkt2: Optional[str]
    shape: List[int]
    transform: Affine

    @classmethod
    def build(cls, dataset: Dataset) -> "DatasetProfile":
        xmin = float(dataset.geospatial_lon_min)
        xmax = float(dataset.geospatial_lon_max)
        if xmin == 0 and xmax == 360:
            # This is a special case where global datasets choose to not go
            # negative with longitudes
            xmin = -180
            xmax = 180
        ymin = float(dataset.geospatial_lat_min)
        ymax = float(dataset.geospatial_lat_max)

        if "projection" in dataset.variables:
            # We can't use the spatial reference attribute, which is WKT,
            # because it doesn't parse valid for sea ice.
            epsg = None
            crs = CRS(dataset.projection.proj4text)
            wkt2 = crs.to_wkt(WktVersion.WKT2_2019)
            shape = [
                int(dataset.projection.parent_grid_cell_row_subset_end),
                int(dataset.projection.parent_grid_cell_column_subset_end),
            ]
            transform = Affine.from_gdal(
                *list(float(s) for s in dataset.projection.GeoTransform.split(" "))
            )
        else:
            epsg = 4326
            crs = CRS("EPSG:4326")
            wkt2 = None
            shape = [int(dataset.sizes["lat"]), int(dataset.sizes["lon"])]
            transform = Affine(
                _parse_resolution(dataset.geospatial_lon_resolution),
                0,
                xmin,
                0,
                -_parse_resolution(dataset.geospatial_lat_resolution),
                ymax,
            )

        return DatasetProfile(
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            epsg=epsg,
            crs=crs,
            wkt2=wkt2,
            shape=shape,
            transform=transform,
        )

    @property
    def bbox(self) -> List[float]:
        return [self.xmin, self.ymin, self.xmax, self.ymax]

    @property
    def geometry(self) -> Any:
        return shapely.geometry.mapping(shapely.geometry.box(*self.bbox))


@dataclass
class BandProfile:
    """Band-level profile used for creating single-band COGs"""

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
        dataset: Dataset,
        variable: str,
        modifier: Optional[Callable[[DataArray], DataArray]] = None,
    ) -> "BandProfile":
        dataset_profile = DatasetProfile.build(dataset)
        data_array = dataset[variable].squeeze()
        if modifier:
            data_array = modifier(data_array)
        data_type = next(
            (d for d in DataType if d.lower() == str(data_array.dtype)), None
        )
        if not data_type:
            raise ValueError(
                f"No raster extension DataType found for numpy dtype: {data_array.dtype}"
            )
        if data_type.startswith("float"):
            nodata: Any = numpy.nan
        else:
            nodata = int(data_array._FillValue)
        if "scale_factor" in data_array.attrs:
            scale = float(data_array.scale_factor)
        else:
            scale = None
        if "add_offset" in data_array.attrs:
            offset = float(data_array.add_offset)
        else:
            offset = None
        if "units" in data_array.attrs:
            unit = data_array.units.replace("_", " ")
        else:
            unit = None
        return cls(
            height=data_array.shape[0],
            width=data_array.shape[1],
            data_type=data_type,
            transform=dataset_profile.transform,
            nodata=nodata,
            crs=dataset_profile.crs,
            scale=scale,
            offset=offset,
            unit=unit,
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


def _parse_resolution(value: Any) -> float:
    if isinstance(value, str):
        # Assume that the first part is a number and the rest are units, e.g. for ocean heat content
        return float(value.split(" ")[0])
    else:
        return float(value)

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, Hashable, List, Optional

import numpy
import shapely.geometry
from pyproj import CRS
from pyproj.enums import WktVersion
from pystac import Asset, MediaType
from pystac.extensions.raster import DataType, NoDataStrings, RasterBand
from rasterio import Affine
from xarray import DataArray, Dataset

UNITLESS = ["unitless", "1"]

# G02202 (sea ice concentration) renamed its grid-mapping variable from
# `projection` (V4) to `crs` (V6). We check for either name so this same
# profile code keeps working across CDR versions/products.
GRID_MAPPING_VARIABLE_NAMES = ("projection", "crs")
X_VARIABLE_NAMES = ("xgrid", "x")
Y_VARIABLE_NAMES = ("ygrid", "y")


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
    needs_longitude_remap: bool
    needs_vertical_flip: bool

    @classmethod
    def build(cls, dataset: Dataset) -> "DatasetProfile":
        xmin = float(dataset.geospatial_lon_min)
        xmax = float(dataset.geospatial_lon_max)
        needs_longitude_remap = False
        if xmin == 0 and xmax == 360:
            # This is a special case where global datasets choose to not go
            # negative with longitudes
            xmin = -180
            xmax = 180
            needs_longitude_remap = True
        ymin = float(dataset.geospatial_lat_min)
        ymax = float(dataset.geospatial_lat_max)

        grid_mapping_name = next(
            (n for n in GRID_MAPPING_VARIABLE_NAMES if n in dataset.variables), None
        )
        if grid_mapping_name is not None:
            grid_mapping = dataset[grid_mapping_name]
            # We can't use the spatial reference attribute, which is WKT,
            # because it doesn't parse valid for sea ice.
            epsg = None
            crs = CRS(grid_mapping.attrs["proj4text"])
            wkt2 = crs.to_wkt(WktVersion.WKT2_2019)
            shape, transform = _grid_geometry(dataset, grid_mapping)
            needs_vertical_flip = False
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
            needs_vertical_flip = True

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
            needs_longitude_remap=needs_longitude_remap,
            needs_vertical_flip=needs_vertical_flip,
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
    nodata: Any
    unit: str
    scale: Optional[float]
    offset: Optional[float]
    attrs: Dict[Hashable, Any]
    title: str
    dataset_profile: DatasetProfile
    variable: str

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
                f"No raster extension DataType found for numpy dtype:"
                f"{data_array.dtype}"
            )
        if data_type.startswith("float"):
            nodata: Any = numpy.nan
        elif "_FillValue" in data_array.attrs:
            nodata = int(data_array._FillValue)
        else:
            # Some variables are documented with "Fill Value: N/A" (e.g. V6's
            # surface_type_mask and daily cdr_melt_onset_day) and genuinely
            # have no _FillValue attribute in the netCDF file.
            nodata = None
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
            if unit in UNITLESS:
                unit = None
        else:
            unit = None
        title = data_array.long_name
        return cls(
            height=data_array.shape[0],
            width=data_array.shape[1],
            data_type=data_type,
            nodata=nodata,
            scale=scale,
            offset=offset,
            unit=unit,
            attrs=data_array.attrs,
            title=title,
            dataset_profile=dataset_profile,
            variable=variable,
        )

    def cog_asset(self, href: str) -> Asset:
        asset = Asset(
            title=self.title, href=href, media_type=MediaType.COG, roles=["data"]
        )
        asset.extra_fields["raster:bands"] = [self.raster_band().to_dict()]
        return asset

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
        if self.nodata is None:
            nodata: Any = None
        elif math.isnan(self.nodata):
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

    @property
    def transform(self) -> Affine:
        return self.dataset_profile.transform

    @property
    def crs(self) -> CRS:
        return self.dataset_profile.crs

    @property
    def needs_longitude_remap(self) -> bool:
        return self.dataset_profile.needs_longitude_remap

    @property
    def needs_vertical_flip(self) -> bool:
        return self.dataset_profile.needs_vertical_flip


def _grid_geometry(dataset: Dataset, grid_mapping: DataArray) -> Any:
    """Returns (shape, transform) for a projected (non-geographic) grid.

    Tries the GDAL-style ``GeoTransform`` attribute on the grid-mapping
    variable first for the transform, since that's present on both V4's
    ``projection`` and V6's ``crs`` variables. Shape comes from
    ``parent_grid_cell_row/column_subset_end`` if present (V4), otherwise
    from the length of the `x`/`y` (or `xgrid`/`ygrid`) coordinate
    variables -- confirmed against a real V6 file that ``crs`` keeps
    `GeoTransform` but no longer has the `parent_grid_cell_*` attrs at all.
    If `GeoTransform` itself is missing, the whole transform is derived
    from the x/y coordinate arrays instead.
    """
    x_name = next((n for n in X_VARIABLE_NAMES if n in dataset.variables), None)
    y_name = next((n for n in Y_VARIABLE_NAMES if n in dataset.variables), None)

    if "GeoTransform" in grid_mapping.attrs:
        transform = Affine.from_gdal(
            *list(float(s) for s in grid_mapping.attrs["GeoTransform"].split(" "))
        )
        if (
            "parent_grid_cell_row_subset_end" in grid_mapping.attrs
            and "parent_grid_cell_column_subset_end" in grid_mapping.attrs
        ):
            shape = [
                int(grid_mapping.attrs["parent_grid_cell_row_subset_end"]),
                int(grid_mapping.attrs["parent_grid_cell_column_subset_end"]),
            ]
        elif x_name is not None and y_name is not None:
            shape = [dataset.sizes[y_name], dataset.sizes[x_name]]
        else:
            raise ValueError(
                "Could not determine grid shape: grid-mapping variable has "
                "GeoTransform but no parent_grid_cell_row/column_subset_end "
                "attrs, and no x/y (or xgrid/ygrid) variables to fall back on."
            )
        return shape, transform

    if x_name is None or y_name is None:
        raise ValueError(
            "Could not determine grid geometry: grid-mapping variable has no "
            "GeoTransform attribute, and no x/y (or xgrid/ygrid) coordinate "
            "variables were found to fall back on."
        )
    x = dataset[x_name].values
    y = dataset[y_name].values
    resolution_x = float(x[1] - x[0])
    resolution_y = float(y[1] - y[0])
    shape = [len(y), len(x)]
    transform = Affine(
        resolution_x,
        0,
        float(x[0] - resolution_x / 2),
        0,
        resolution_y,
        float(y[0] - resolution_y / 2),
    )
    return shape, transform


def _parse_resolution(value: Any) -> float:
    if isinstance(value, str):
        # Assume that the first part is a number and the rest are units,
        # e.g. for ocean heat content
        return float(value.split(" ")[0])
    else:
        return float(value)

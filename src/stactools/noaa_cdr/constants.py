import shapely.geometry
from pystac import CatalogType, Provider, ProviderRole, SpatialExtent

GLOBAL_BBOX = [-180.0, -90.0, 180.0, 90.0]
GLOBAL_GEOMETRY = shapely.geometry.mapping(shapely.geometry.box(*GLOBAL_BBOX))
GLOBAL_SPATIAL_EXTENT = SpatialExtent(bboxes=GLOBAL_BBOX)
PROVIDERS = [
    Provider(
        name="National Centers for Environmental Information",
        description="NCEI is the Nation's leading authority for environmental data,"
        " and manage "
        "one of the largest archives of atmospheric, coastal, geophysical, and "
        "oceanic research in the world. NCEI contributes to the NESDIS mission "
        "by developing new products and services that span the science disciplines "
        "and enable better data discovery.",
        roles=[
            ProviderRole.PRODUCER,
            ProviderRole.PROCESSOR,
            ProviderRole.LICENSOR,
            ProviderRole.HOST,
        ],
        url="https://www.ncei.noaa.gov/",
    )
]
LICENSE = "proprietary"
DEFAULT_CATALOG_TYPE = CatalogType.SELF_CONTAINED
PROCESSING_EXTENSION_SCHEMA = (
    "https://stac-extensions.github.io/processing/v1.1.0/schema.json"
)
CLASSIFICATION_EXTENSION_SCHEMA = (
    "https://stac-extensions.github.io/classification/v1.1.0/schema.json"
)
NETCDF_ASSET_KEY = "netcdf"
COMMON_KEYWORDS = ["Global", "Climate", "NOAA"]
INTERVAL_ATTRIBUTE_NAME = "noaa_cdr:interval"
MAX_DEPTH_ATTRIBUTE_NAME = "noaa_cdr:max_depth"

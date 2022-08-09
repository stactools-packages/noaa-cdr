from enum import Enum


class Names(str, Enum):
    # https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content
    OceanHeatContent = "ocean-heat-content"

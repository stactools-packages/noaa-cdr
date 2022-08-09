from enum import Enum, unique
from typing import List


@unique
class Name(str, Enum):
    # https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content
    OceanHeatContent = "ocean-heat-content"


def hrefs(name: Name) -> List[str]:
    """Returns all asset hrefs for the given CDR name.

    Args:
        name (str): The CDR Name.

    Returns:
        List[str]: The CDR hrefs.
    """
    hrefs = []
    if name == Name.OceanHeatContent:
        for variable in [
            "heat_content",
            "mean_halosteric_sea_level",
            "mean_salinity",
            "mean_temperature",
            "mean_thermosteric_sea_level",
            "mean_total_steric_sea_level",
        ]:
            for depth in ["700", "2000"]:
                for period in ["monthly", "pentad", "seasonal", "yearly"]:
                    if period == "monthly" and variable != "heat_content":
                        continue
                    hrefs.append(
                        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data/0164586/"
                        f"derived/{variable}_anomaly_0-{depth}_{period}.nc"
                    )
    return hrefs

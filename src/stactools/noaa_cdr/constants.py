from enum import Enum, unique
from typing import List


@unique
class Name(str, Enum):
    # https://www.ncei.noaa.gov/products/climate-data-records/global-ocean-heat-content
    OceanHeatContent = "ocean-heat-content"


@unique
class TimeResolution(str, Enum):
    """Used to parse ``time_coverage_resolution`` in NetCDF files.

    We _could_ use a real datetime package, e.g. pandas's Timedelta, but since
    we only need to handle four cases, this simple structure seemed easier.
    """

    Monthly = "P01M"
    Seasonal = "P03M"
    Yearly = "P01Y"
    Pentadal = "P05Y"

    @classmethod
    def from_value(cls, value: str) -> "TimeResolution":
        """Finds the TimeResolution that matches the provided value.

        Args:
            value (str): The string value of the TimeResolution, per NetCDF standard.

        Returns:
            TimeResolution: The resolved time resolution.

        Raises:
            ValueError: Raised if the value is not a valid TimeResolution.
        """
        time_resolution = next(
            (t for t in TimeResolution if t.value == value),
            None,
        )
        if time_resolution is None:
            raise ValueError(
                "Encountered unexpected time_coverage_resolution: " f"{value}"
            )
        else:
            return time_resolution


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
            for depth in ["100", "700", "2000"]:
                for period in ["monthly", "pentad", "seasonal", "yearly"]:
                    if period == "monthly" and variable != "heat_content":
                        continue
                    elif depth == "100" and variable not in [
                        "mean_salinity",
                        "mean_temperature",
                    ]:
                        continue
                    hrefs.append(
                        "https://www.ncei.noaa.gov/data/oceans/ncei/archive/data/0164586/"
                        f"derived/{variable}_anomaly_0-{depth}_{period}.nc"
                    )
    return hrefs

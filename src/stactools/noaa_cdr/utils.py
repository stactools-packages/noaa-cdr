import datetime
import math

import dateutil.relativedelta
import xarray

from .constants import TimeResolution


def add_months_to_datetime(
    base_time: datetime.datetime, months: float
) -> datetime.datetime:
    """Adds a (possibly fractional) number of months to a datetime.

    Dateutil's relativedelta does not handle fractional numbers of months:
    https://dateutil.readthedocs.io/en/stable/relativedelta.html. This utility
    function enables fractional month offsets.

    Args:
        base_time (datetime.datetime): The start datetime.
        months (float): The number of months to advance.

    Returns:
        datetime.datetime: The new datetime.
    """
    fractional_months, integer_months = math.modf(months)
    time = base_time + dateutil.relativedelta.relativedelta(months=int(integer_months))
    if fractional_months != 0.0:
        time_in_seconds = time.timestamp()
        next_month_in_seconds = (
            time + dateutil.relativedelta.relativedelta(months=1)
        ).timestamp()
        return time + dateutil.relativedelta.relativedelta(
            seconds=int((next_month_in_seconds - time_in_seconds) * fractional_months)
        )
    else:
        return time


def time_interval_as_str(
    time: datetime.datetime, time_resolution: TimeResolution
) -> str:
    """Returns the given time interval as a string.

    Yearly and monthly values are turned into simple strings, e.g. "2020" and
    "2020-06", respectively. Pentadal are turned into a five-year interval with
    an exclusive top bound, e.g. "2018-2023". Seasonal values are given a "Q1",
    "Q2", "Q3", or "Q4" suffix.

    Args:
        time (datetime.datetime): The center time in the interval.
        time_resolution (TimeResolution): The length of the interval.

    Returns:
        str: The time interval as a string.
    """
    if time_resolution is TimeResolution.Monthly:
        return time.strftime("%Y-%m")
    elif time_resolution is TimeResolution.Seasonal:
        season = _month_to_season(time.month)
        return f"{time.year}-{season}"
    elif time_resolution is TimeResolution.Yearly:
        return time.strftime("%Y")
    elif time_resolution is TimeResolution.Pentadal:
        return f"{time.year - 2}-{time.year + 3}"
    else:
        raise NotImplementedError


def data_variable_name(dataset: xarray.Dataset) -> str:
    """Returns the variable name that points to a four-dimensional data array.

    Args:
        dataset (xarray.Dataset): An open xarray Dataset

    Returns:
        str: The variable name.
    """
    for variable in dataset.variables:
        if len(dataset[variable].sizes) == 4:
            return str(variable)
    raise Exception("No 4-dimensional variable found in this dataset.")


def _month_to_season(month: int) -> str:
    if month in (1, 2, 3):
        return "Q1"
    elif month in (4, 5, 6):
        return "Q2"
    elif month in (7, 8, 9):
        return "Q3"
    else:
        return "Q4"


def asset_key_to_title(key: str) -> str:
    """Converts an asset key to a human-readable title.

    Args:
        key (str): The asset key.

    Returns:
        str: The title.
    """
    return key.replace("_", " ").capitalize()

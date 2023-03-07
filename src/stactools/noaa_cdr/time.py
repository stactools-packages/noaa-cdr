import datetime
import math
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

import dateutil.relativedelta
import numpy
from dateutil.tz import tzutc


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


def datetime64_to_datetime(datetime64: numpy.datetime64) -> datetime.datetime:
    # https://stackoverflow.com/a/46921593/732529
    unix_epoch = numpy.datetime64(0, "s")
    one_second = numpy.timedelta64(1, "s")
    seconds_since_epoch = float((datetime64 - unix_epoch) / one_second)
    dt = datetime.datetime.utcfromtimestamp(seconds_since_epoch)
    return dt.replace(tzinfo=tzutc())


class TimeResolution(str, Enum):
    """Used to parse ``time_coverage_resolution`` in NetCDF files.
    We _could_ use a real datetime package, e.g. pandas's Timedelta, but since
    we only need to handle four cases, this simple structure seemed easier.
    """

    ThreeHourly = "PT3H"
    Daily = "P1D"
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
            # Sea ice uses P1M for monthly instead of P01M
            if value == "P1M":
                return TimeResolution.Monthly
            else:
                raise ValueError(
                    "Encountered unexpected time_coverage_resolution: " f"{value}"
                )
        else:
            return time_resolution

    def datetime_bounds(
        self, dt: datetime.datetime
    ) -> Tuple[datetime.datetime, datetime.datetime]:
        """Returns the start and end datetimes for a given datetime and time resolution.

        E.g. if the time resolution is yearly, the start datetime will be 01 Jan,
        and the end datetime will be 31 Dec one second before midnight.

        Args:
            dt (datetime.datetime): The reference datetime.
        Returns
            Tuple[datetime.datetime, datetime.datetime]: start_datetime and
                end_datetime as a two-tuple.
        """
        if self is TimeResolution.Monthly:
            start_datetime = datetime.datetime(dt.year, dt.month, 1)
            return (
                start_datetime,
                start_datetime
                + dateutil.relativedelta.relativedelta(months=+1, seconds=-1),
            )
        elif self is TimeResolution.Seasonal:
            season = _month_to_season(dt.month)
            if season == "Q1":
                start_month = 1
            elif season == "Q2":
                start_month = 4
            elif season == "Q3":
                start_month = 7
            elif season == "Q4":
                start_month = 10
            else:
                raise NotImplementedError
            start_datetime = datetime.datetime(dt.year, start_month, 1)
            return (
                start_datetime,
                start_datetime
                + dateutil.relativedelta.relativedelta(months=+3, seconds=-1),
            )
        elif self is TimeResolution.Yearly:
            return (
                datetime.datetime(dt.year, 1, 1),
                datetime.datetime(dt.year, 12, 31, 23, 59, 59),
            )
        elif self is TimeResolution.Pentadal:
            return (
                datetime.datetime(dt.year - 2, 1, 1),
                datetime.datetime(dt.year + 2, 12, 31, 23, 59, 59),
            )
        else:
            raise NotImplementedError

    def as_str(self, dt: datetime.datetime) -> str:
        """Returns the given time interval as a string.

        Yearly and monthly values are turned into simple strings, e.g. "2020" and
        "2020-06", respectively. Pentadal are turned into a five-year interval with
        an exclusive top bound, e.g. "2018-2023". Seasonal values are given a "Q1",
        "Q2", "Q3", or "Q4" suffix.

        Args:
            dt (datetime.datetime): The center time in the interval.
        Returns:
            str: The time interval as a string.
        """
        if self is TimeResolution.Monthly:
            return dt.strftime("%Y-%m")
        elif self is TimeResolution.Seasonal:
            season = _month_to_season(dt.month)
            return f"{dt.year}-{season}"
        elif self is TimeResolution.Yearly:
            return dt.strftime("%Y")
        elif self is TimeResolution.Pentadal:
            return f"{dt.year - 2}-{dt.year + 2}"
        elif self is TimeResolution.Daily:
            return dt.strftime(r"%Y-%m-%d")
        else:
            raise NotImplementedError

    def to_interval(self) -> str:
        """Returns this time resolution as a slug-like string.

        Used for the `noaa_cdr:interval` attribute on items.

        Returns:
            str: This time resolution as a string.
        """
        if self is TimeResolution.Monthly:
            return "monthly"
        elif self is TimeResolution.Seasonal:
            return "seasonal"
        elif self is TimeResolution.Yearly:
            return "yearly"
        elif self is TimeResolution.Pentadal:
            return "pentadal"
        elif self is TimeResolution.Daily:
            return "daily"
        elif self is TimeResolution.ThreeHourly:
            return "three-hourly"
        else:
            raise NotImplementedError


@dataclass
class TimeDuration:
    """Used to parse ``time_coverage_duration`` in NetCDF files.
    We _could_ use a real datetime package, e.g. pandas's Timedelta, but since
    we only need to handle four cases, this simple structure seemed easier.
    """

    count: int
    unit: str

    @classmethod
    def parse(cls, s: str) -> "TimeDuration":
        assert s.startswith("P")
        count = int(s[1:-1])
        unit = s[-1]
        return TimeDuration(count=count, unit=unit)

    def end_datetime(self, start_datetime: datetime.datetime) -> datetime.datetime:
        if self.unit == "Y":
            delta = dateutil.relativedelta.relativedelta(years=self.count)
        elif self.unit == "M":
            delta = dateutil.relativedelta.relativedelta(months=self.count)
        else:
            raise ValueError(f"Unrecognized time duration unit: {self.unit}")
        return start_datetime + delta - dateutil.relativedelta.relativedelta(seconds=1)


def _month_to_season(month: int) -> str:
    if month in (1, 2, 3):
        return "Q1"
    elif month in (4, 5, 6):
        return "Q2"
    elif month in (7, 8, 9):
        return "Q3"
    else:
        return "Q4"

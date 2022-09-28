import datetime
from typing import Tuple

import pytest

from stactools.noaa_cdr import time
from stactools.noaa_cdr.time import TimeResolution


def test_add_months_to_datetime_integer() -> None:
    base_time = datetime.datetime(2022, 1, 1)
    dt = time.add_months_to_datetime(base_time, 42)
    assert dt == datetime.datetime(2025, 7, 1)


def test_add_months_to_datetime_fractional() -> None:
    base_time = datetime.datetime(2022, 1, 1)
    dt = time.add_months_to_datetime(base_time, 42.5)
    assert dt == datetime.datetime(2025, 7, 16, 12)


@pytest.mark.parametrize(
    "time,time_resolution,expected",
    [
        (
            datetime.datetime(2022, 6, 15),
            TimeResolution.Monthly,
            (datetime.datetime(2022, 6, 1), datetime.datetime(2022, 6, 30, 23, 59, 59)),
        ),
        (
            datetime.datetime(2022, 2, 15),
            TimeResolution.Seasonal,
            (datetime.datetime(2022, 1, 1), datetime.datetime(2022, 3, 31, 23, 59, 59)),
        ),
        (
            datetime.datetime(2022, 7, 15),
            TimeResolution.Yearly,
            (
                datetime.datetime(2022, 1, 1),
                datetime.datetime(2022, 12, 31, 23, 59, 59),
            ),
        ),
        (
            datetime.datetime(2022, 6, 15),
            TimeResolution.Pentadal,
            (
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2024, 12, 31, 23, 59, 59),
            ),
        ),
    ],
)
def test_datetime_bounds(
    time: datetime.datetime,
    time_resolution: TimeResolution,
    expected: Tuple[datetime.datetime, datetime.datetime],
) -> None:
    assert time_resolution.datetime_bounds(time) == expected


@pytest.mark.parametrize(
    "time,time_resolution,expected",
    [
        (datetime.datetime(2022, 6, 15), TimeResolution.Monthly, "2022-06"),
        (datetime.datetime(2022, 2, 15), TimeResolution.Seasonal, "2022-Q1"),
        (datetime.datetime(2022, 7, 15), TimeResolution.Yearly, "2022"),
        (datetime.datetime(2022, 7, 15), TimeResolution.Pentadal, "2020-2024"),
    ],
)
def test_time_interval_as_str(
    time: datetime.datetime, time_resolution: TimeResolution, expected: str
) -> None:
    assert time_resolution.as_str(time) == expected

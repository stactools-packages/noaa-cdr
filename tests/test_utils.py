import datetime

import pytest

from stactools.noaa_cdr import utils
from stactools.noaa_cdr.constants import TimeResolution


def test_add_months_to_datetime_integer() -> None:
    base_time = datetime.datetime(2022, 1, 1)
    time = utils.add_months_to_datetime(base_time, 42)
    assert time == datetime.datetime(2025, 7, 1)


def test_add_months_to_datetime_fractional() -> None:
    base_time = datetime.datetime(2022, 1, 1)
    time = utils.add_months_to_datetime(base_time, 42.5)
    assert time == datetime.datetime(2025, 7, 16, 12)


@pytest.mark.parametrize(
    "time,time_resolution,expected",
    [
        (datetime.datetime(2022, 6, 15), TimeResolution.Monthly, "2022-06"),
        (datetime.datetime(2022, 2, 15), TimeResolution.Seasonal, "2022-Winter"),
        (datetime.datetime(2022, 7, 15), TimeResolution.Yearly, "2022"),
        (datetime.datetime(2022, 7, 15), TimeResolution.Pentadal, "2020-2024"),
    ],
)
def test_time_interval_as_str(
    time: datetime.datetime, time_resolution: TimeResolution, expected: str
) -> None:
    assert utils.time_interval_as_str(time, time_resolution) == expected

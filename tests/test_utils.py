import datetime

from stactools.noaa_cdr import utils


def test_add_months_to_datetime_integer() -> None:
    base_time = datetime.datetime(2022, 1, 1)
    time = utils.add_months_to_datetime(base_time, 42)
    assert time == datetime.datetime(2025, 7, 1)


def test_add_months_to_datetime_fractional() -> None:
    base_time = datetime.datetime(2022, 1, 1)
    time = utils.add_months_to_datetime(base_time, 42.5)
    assert time == datetime.datetime(2025, 7, 16, 12)

import datetime

import pytest
import xarray

from stactools.noaa_cdr import utils
from stactools.noaa_cdr.constants import TimeResolution
from tests import test_data


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
        (datetime.datetime(2022, 2, 15), TimeResolution.Seasonal, "2022-Q1"),
        (datetime.datetime(2022, 7, 15), TimeResolution.Yearly, "2022"),
        (datetime.datetime(2022, 7, 15), TimeResolution.Pentadal, "2020-2024"),
    ],
)
def test_time_interval_as_str(
    time: datetime.datetime, time_resolution: TimeResolution, expected: str
) -> None:
    assert utils.time_interval_as_str(time, time_resolution) == expected


def test_data_variable_name() -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    with xarray.open_dataset(path, decode_times=False) as dataset:
        assert utils.data_variable_name(dataset) == "h18_hc"

    path = test_data.get_external_data(
        "mean_halosteric_sea_level_anomaly_0-2000_yearly.nc"
    )
    with xarray.open_dataset(path, decode_times=False) as dataset:
        assert utils.data_variable_name(dataset) == "b_mm_hs"

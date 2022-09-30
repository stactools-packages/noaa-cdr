import pytest
import xarray

from stactools.noaa_cdr import dataset

from . import test_data


def test_data_variable_name() -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    with xarray.open_dataset(path, decode_times=False) as ds:
        assert dataset.data_variable_name(ds) == "h18_hc"

    path = test_data.get_external_data(
        "mean_halosteric_sea_level_anomaly_0-2000_yearly.nc"
    )
    with xarray.open_dataset(path, decode_times=False) as ds:
        assert dataset.data_variable_name(ds) == "b_mm_hs"

    path = test_data.get_external_data("oisst-avhrr-v02r01.20220913.nc")
    with xarray.open_dataset(path) as ds:
        with pytest.raises(ValueError):
            dataset.data_variable_name(ds)


def test_data_variable_names() -> None:
    path = test_data.get_external_data("oisst-avhrr-v02r01.20220913.nc")
    with xarray.open_dataset(path) as ds:
        assert set(dataset.data_variable_names(ds)) == {
            "sst",
            "anom",
            "err",
            "ice",
        }

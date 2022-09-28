import xarray

from stactools.noaa_cdr import utils

from . import test_data


def test_data_variable_name() -> None:
    path = test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")
    with xarray.open_dataset(path, decode_times=False) as dataset:
        assert utils.data_variable_name(dataset) == "h18_hc"

    path = test_data.get_external_data(
        "mean_halosteric_sea_level_anomaly_0-2000_yearly.nc"
    )
    with xarray.open_dataset(path, decode_times=False) as dataset:
        assert utils.data_variable_name(dataset) == "b_mm_hs"

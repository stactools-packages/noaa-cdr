import pytest

from stactools.noaa_cdr.sea_ice_concentration import stac

from .. import test_data


@pytest.mark.parametrize(
    "file_name",
    [
        ("seaice_conc_daily_nh_20211231_f17_v04r00.nc"),
        ("seaice_conc_daily_sh_20211231_f17_v04r00.nc"),
        ("seaice_conc_monthly_nh_202112_f17_v04r00.nc"),
        ("seaice_conc_monthly_sh_202112_f17_v04r00.nc"),
    ],
)
def test_create_item(file_name: str) -> None:
    path = test_data.get_path(f"data-files/{file_name}")
    item = stac.create_item(path)
    item.validate()

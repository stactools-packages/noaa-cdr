import xarray

from stactools.noaa_cdr.profile import BandProfile

from . import test_data


def test_shape() -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    with xarray.open_dataset(path) as dataset:
        band_profile = BandProfile.build(dataset, "cdr_seaice_conc")
    assert band_profile.shape == [448, 304]


def test_title() -> None:
    path = test_data.get_path("data-files/seaice_conc_daily_nh_20211231_f17_v04r00.nc")
    with xarray.open_dataset(path) as dataset:
        band_profile = BandProfile.build(dataset, "cdr_seaice_conc")
    assert band_profile.title == (
        "NOAA/NSIDC Climate Data Record of Passive Microwave Daily Northern "
        "Hemisphere Sea Ice Concentration"
    )

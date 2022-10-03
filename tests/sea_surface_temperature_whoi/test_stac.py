from stactools.noaa_cdr.sea_surface_temperature_whoi import stac

from .. import test_data


def test_create_item() -> None:
    path = test_data.get_external_data(
        "SEAFLUX-OSB-CDR_V02R00_SST_D20210831_C20211223.nc"
    )
    item = stac.create_item(path)
    item.validate()

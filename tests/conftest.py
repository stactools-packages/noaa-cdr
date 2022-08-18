import os.path

import pytest

from stactools.noaa_cdr.cdr import OceanHeatContent
from tests import test_data


@pytest.fixture(scope="class")
def external_data(request: pytest.FixtureRequest) -> None:
    request.cls.netcdf_path_for_cogify = test_data.get_external_data(
        "heat_content_anomaly_0-2000_yearly.nc"
    )


@pytest.fixture
def cogify_href() -> str:
    return next(
        href
        for href in OceanHeatContent.hrefs()
        if os.path.basename(href) == "heat_content_anomaly_0-2000_yearly.nc"
    )

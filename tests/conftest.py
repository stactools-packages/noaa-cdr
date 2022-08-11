import pytest

from tests import test_data


@pytest.fixture
def netcdf_path_for_cogify() -> str:
    return test_data.get_external_data("heat_content_anomaly_0-2000_yearly.nc")


@pytest.fixture(scope="class")
def external_data(request: pytest.FixtureRequest) -> None:
    request.cls.netcdf_path_for_cogify = test_data.get_external_data(
        "heat_content_anomaly_0-2000_yearly.nc"
    )

import os.path
from typing import List

import pytest
from pytest import Config, FixtureRequest, Item, Parser

from stactools.noaa_cdr.cdr import OceanHeatContent
from tests import test_data


@pytest.fixture(scope="class")
def external_data(request: FixtureRequest) -> None:
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


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--slow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

from typing import Any

import pytest
from pytest import Config, Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--external-data",
        action="store_true",
        default=False,
        help="run tests that require external data",
    )


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers",
        "external_data: marks tests requiring external data, "
        "and disables them by default (enable with --external-data)",
    )


def pytest_collection_modifyitems(config: Config, items: Any) -> None:
    if config.getoption("--external-data"):
        return
    skip_network_access = pytest.mark.skip(reason="need --external-data option to run")
    for item in items:
        if "external_data" in item.keywords:
            item.add_marker(skip_network_access)

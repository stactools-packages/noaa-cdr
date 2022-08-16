import os.path
from typing import Any, Dict

from stactools.testing.test_data import TestData

from stactools.noaa_cdr import constants
from stactools.noaa_cdr.constants import Cdr

external_data: Dict[str, Any] = dict()

for href in constants.hrefs(Cdr.OceanHeatContent):
    external_data[os.path.basename(href)] = {"url": href}

test_data = TestData(__file__, external_data)

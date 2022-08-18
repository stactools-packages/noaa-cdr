import os.path
from typing import Any, Dict

from stactools.testing.test_data import TestData

from stactools.noaa_cdr.cdr import OceanHeatContent

external_data: Dict[str, Any] = dict()

for href in OceanHeatContent.hrefs():
    external_data[os.path.basename(href)] = {"url": href}

test_data = TestData(__file__, external_data)

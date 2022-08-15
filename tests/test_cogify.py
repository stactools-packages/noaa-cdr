import os.path
from tempfile import TemporaryDirectory

import pytest

from stactools import noaa_cdr
from tests import test_data

COGIFY_PARAMETERS = [("heat_content_anomaly_0-2000_yearly.nc", 17)]


@pytest.mark.parametrize("infile,num_cogs", COGIFY_PARAMETERS)
def test_cogify(infile: str, num_cogs: int) -> None:
    external_data_path = test_data.get_external_data(infile)
    with TemporaryDirectory() as temporary_directory:
        paths = noaa_cdr.cogify(external_data_path, temporary_directory)
        assert len(paths) == num_cogs
        for path in paths:
            assert os.path.exists(path)

import os.path
from tempfile import TemporaryDirectory

from stactools import noaa_cdr


def test_cogify(netcdf_path_for_cogify: str) -> None:
    with TemporaryDirectory() as temporary_directory:
        paths = noaa_cdr.cogify(netcdf_path_for_cogify, temporary_directory)
        assert len(paths) == 17
        for path in paths:
            assert os.path.exists(path)

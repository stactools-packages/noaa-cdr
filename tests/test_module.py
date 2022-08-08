import stactools.noaa_cdr


def test_version() -> None:
    assert stactools.noaa_cdr.__version__ is not None

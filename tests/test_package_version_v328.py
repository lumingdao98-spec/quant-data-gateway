from quant_data import __version__


def test_package_version_matches_current_release() -> None:
    assert __version__ == "3.28.0"

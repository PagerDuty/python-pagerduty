import sys

def derived_version():
    if sys.version_info.major == 3 and sys.version_info.minor < 8:
        # There is no way to derive the version from the package metadata because the
        # necessary importlib features have not yet been added. At some point we need to
        # drop support for these versions so that we can stop updating this version
        # manually in two places and set the version in only one place, pyproject.toml
        return "2.0.0"
    else:
        from importlib.metadata import version
        return version(__package__)

__version__ = derived_version()

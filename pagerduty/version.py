import os
import sys

UNKNOWN_VERSION = "7.*.*"


def pyproject_toml_path():
    return os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        "pyproject.toml",
    )


def get_version_via_tomllib():
    import tomllib

    with open(pyproject_toml_path(), "rb") as f:
        pkg_meta = tomllib.load(f)
        return pkg_meta.get("project", {}).get("version", UNKNOWN_VERSION)


def get_version():
    if os.path.exists(pyproject_toml_path()):
        # No package has been built/installed yet, so this is a stopgap to
        # avoid errors in local unit tests and documentation builds:
        if sys.version_info.minor < 11:
            # tomllib was introduced in 3.11 and cannot be used here
            return UNKNOWN_VERSION
        else:
            # Use tomllib so the correct version number goes into the doc
            # build:
            return get_version_via_tomllib()
    else:
        # Use package metadata introspection to get the version:
        from importlib.metadata import version

        return version(__package__)


__version__ = get_version()

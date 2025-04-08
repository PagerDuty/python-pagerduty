import os
import sys

UNKNOWN_VERSION = "2.*.*"

def get_version_via_tomllib():
    import tomllib
    base_project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    with open(os.path.join(base_project_path, 'pyproject.toml'), 'rb') as f:
        pkg_meta = tomllib.load(f)
        return pkg_meta.get('project', {}).get('version', UNKNOWN_VERSION)

def get_version():
    if sys.version_info.major == 3 and sys.version_info.minor < 8:
        # There is no way to obtain the version from the package metadata because the
        # necessary importlib features have not yet been added. At some point we need to
        # drop support for these versions. We only care about major version 3 because
        # version 2 is already not supported.
        return UNKNOWN_VERSION
    else:
        try:
            # Use package metadata introspection to get the version:
            from importlib.metadata import version
            return version(__package__)
        except:
            # No package has been built/installed yet, so this is a stopgap to avoid
            # errors in local unit tests and documentation builds:
            if sys.version_info.minor < 11:
                # tomllib was introduced in 3.11
                return UNKNOWN_VERSION
            else:
                # Use tomllib so the correct version number goes into the doc build:
                return get_version_via_tomllib()

__version__ = get_version()

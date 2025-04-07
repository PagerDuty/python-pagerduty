import sys

def get_version():
    if sys.version_info.major == 3 and sys.version_info.minor < 8:
        # There is no way to obtain the version from the package metadata because the
        # necessary importlib features have not yet been added. At some point we need to
        # drop support for these versions. We only care about major version 3 because
        # version 2 is already not supported.
        return "2.x.x"
    else:
        try:
            from importlib.metadata import version
            return version(__package__)
        except:
            # No package has been built/installed locally yet, so this is a stopgap to
            # avoid errors in CI/CD tests:
            return "*.*.*-LOCAL-IMPORT-UNIT-TEST"

__version__ = get_version()

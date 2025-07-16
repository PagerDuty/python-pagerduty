import sys
import unittest

import pagerduty

class VersionTest(unittest.TestCase):

    def test_major_version(self):
        """
        Validate that the major component of "unknown version" matches the actual

        This ensures we have something to track major versions with, in Python versions
        where package introspection isn't available.

        The test is tautological and won't even run in versions less than 11
        (ImportError) because tomllib was added in version 3.11. However, we only need to see it fail in one version to know that it
        needs to be updated. This is because the get_version() method uses tomllib
        (added in 3.11) to extract the version from pyproject.toml i.e. when running in
        a unit test, because the package may not have been built yet depending on the
        test environment (and this is required for using importlib)
        """
        if sys.version_info.major == 3 and sys.version_info.minor > 10:
            ver_in_toml = pagerduty.version.get_version_via_tomllib()
            ver_unknown = pagerduty.version.UNKNOWN_VERSION
            ver_from_fn = pagerduty.version.get_version()
            self.assertEqual(*[v.split('.')[0] for v in (ver_in_toml, ver_unknown)])
            self.assertEqual(*[v.split('.')[0] for v in (ver_unknown, ver_from_fn)])

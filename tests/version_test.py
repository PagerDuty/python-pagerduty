import unittest

import pagerduty

class VersionTest(unittest.TestCase):

    def major_version_test(self):
        """
        Validate that the major "unknown version" matches the same as the actual

        This ensures we have something to track major versions with.

        It is tautological in versions less than 11, but we only need to see it fail in
        one version to know that it needs to be updated. This is because the
        get_version() method uses tomllib to extract the version from pyproject.toml
        i.e. when running in a unit test, because the package may not have been built
        yet depending on the test environment (and this is required for using importlib)
        """
        ver_in_toml = pagerduty.version.get_version_via_tomllib()
        ver_unknown = pagerdut.version.UNKNOWN_VERSION
        ver_from_fn = pagerduty.version.get_version()
        self.assertEqual(*[v.split('.')[0] for v in (ver_in_toml, ver_unknown)])
        self.assertEqual(*[v.split('.')[0] for v in (ver_unknown, ver_from_fn)])


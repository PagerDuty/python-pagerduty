"""
Tests for methods in the common module, and common utilities for other tests.

Note, both of the imports of top-level pagerduty and the common module from
pagerduty are needed; they validate that the top level module has the
interfaces to the common methods. This is to remain until we can deprecate and
finally remove these published interfaces (breaking changes) so that the core
of the client isn't exposed and stops accumulating external dependency.
"""

import datetime
import json
import unittest
from datetime import timezone

from mocks import Client, Response


import pagerduty
from pagerduty import common


class ClientTest(unittest.TestCase):
    """
    A base class for testing client classes in the ``pagerduty`` library

    It mainly serves as a collection of common methods.
    """

    def assertDictContainsSubset(self, d0, d1):
        d0_keys = list(dict(d0).keys())
        d1_keys = list(dict(d1).keys())
        self.assertTrue(
            set(d0_keys).issubset(set(d1_keys)),
            msg=f"First dict (keys={d0_keys}) is not a subset of second dict "
            f"(keys={d1_keys})",
        )
        self.assertEqual(d0, dict([(k, d1[k]) for k in d0]))

    def assertDictContainsCaseInsensitiveSubset(self, d0, d1):
        self.assertDictContainsSubset(
            {k.lower(): v for (k, v) in d0.items()},
            {k.lower(): v for (k, v) in d1.items()},
        )


class CommonTest(unittest.TestCase):
    """
    Tests for functions in the common module
    """

    def test_datetime_intervals(self):
        # Fall back to 1s / no. of seconds for intervals if the interval is too short
        start = datetime.datetime(
            year=2025, month=7, day=1, hour=0, minute=0, second=0
        )
        end = datetime.datetime(
            year=2025, month=7, day=1, hour=0, minute=0, second=3
        )
        intervals = pagerduty.common.datetime_intervals(start, end)
        # The start and end must line up with the original arguments:
        self.assertEqual(start, intervals[0][0])
        self.assertEqual(end, intervals[-1][1])
        self.assertEqual(3, len(intervals))
        for intl_start, intl_end in intervals:
            self.assertEqual(1, int((intl_end - intl_start).total_seconds()))
        # If the interval cannot be evenly divided among sub-intervals:
        end = datetime.datetime(
            year=2025, month=7, day=1, hour=0, minute=1, second=0
        )
        intervals = pagerduty.common.datetime_intervals(start, end, n=7)
        # There should be the specified number of intervals:
        self.assertEqual(7, len(intervals))
        # The start and end must line up with the original arguments:
        self.assertEqual(start, intervals[0][0])
        self.assertEqual(end, intervals[-1][1])
        # - The length of each sub-interval except the last is the quotient
        # - The total combined length of intervals must still equal the length of the
        # original interval given
        # - The final interval is the remainder after subtracting (n-1)*q from the total
        # interval length. In this case: 60 seconds total, 7*8 second intervals, but the
        # last one ends up being 12 seconds because the first 6 intervals bring us to
        # the :48 second mark:
        total_s = 0
        for i, (intl_start, intl_end) in enumerate(intervals):
            if i == len(intervals) - 1:
                break
            interval_len = (intl_end - intl_start).total_seconds()
            self.assertEqual(8, int(interval_len))
            total_s += interval_len
            self.assertEqual(
                intl_end,
                intervals[i + 1][0],
                msg="Time intervals must be consecutive and non-overlapping.",
            )
        interval_len = (intervals[-1][1] - intervals[-1][0]).total_seconds()
        total_s += interval_len
        self.assertEqual(12, int(interval_len))
        self.assertEqual((end - start).total_seconds(), total_s)

    def test_datetime_conversion(self):
        """
        Tests relative_seconds_to_datetime and datetime_to_relative_seconds.

        These two methods basically are inverse functions of each other.

        Note: this test might be flaky, if something causes a serious delay in
        the execution of any of the underlying Python methods. It is a test of
        two methods, which should be the inverse of each other, but since
        datetime.datetime.now is immutable, we can't use patch.object to mock
        it so the best I could come up with for now is to assert that the
        relative number of seconds in-between changing it to a timestamp in the
        future and turning that back into a number of seconds relative to the
        new time afterwards is very close to the original.

        To fix this, we
        """
        t0 = 86400
        future_timestamp = common.relative_seconds_to_datetime(t0)
        t1 = common.datetime_to_relative_seconds(future_timestamp)
        self.assertTrue(abs(t1 - t0) / t0 < 0.0001)

    def test_normalize_url(self):
        urls_expected = [
            (
                ("https://api.pagerduty.com/", "users"),
                "https://api.pagerduty.com/users",
            ),
            (
                ("https://api.pagerduty.com", "/users"),
                "https://api.pagerduty.com/users",
            ),
            (
                (
                    "https://api.pagerduty.com",
                    "https://api.pagerduty.com/users",
                ),
                "https://api.pagerduty.com/users",
            ),
        ]
        for base_url_url, expected_url in urls_expected:
            self.assertEqual(
                expected_url, pagerduty.normalize_url(*base_url_url)
            )
        invalid_input = [  # URL does not start with base_url
            (
                "https://api.pagerduty.com/incidents",
                "https://events.pagerduty.com/api/v2/enqueue",
            ),
            (
                "https://api.pagerduty.com/services",
                "https://some.shady-site.com/read-auth-headers",
            ),
        ]
        for args in invalid_input:
            self.assertRaises(
                pagerduty.UrlError, pagerduty.normalize_url, *args
            )

    def test_plural_deplural(self):
        # forward
        for r_name in ("escalation_policies", "services", "log_entries"):
            self.assertEqual(
                r_name, pagerduty.plural_name(pagerduty.singular_name(r_name))
            )
        # reverse
        for o_name in ("escalation_policy", "service", "log_entry"):
            self.assertEqual(
                o_name, pagerduty.singular_name(pagerduty.plural_name(o_name))
            )

    def test_strftime(self):
        when = datetime.datetime(2025, 7, 1, 23, 19, tzinfo=timezone.utc)
        datestr = pagerduty.common.strftime(when)
        self.assertEqual("0000", datestr[-4:])
        self.assertEqual("2025", datestr[:4])
        self.assertEqual("07", datestr[5:7])
        self.assertEqual("01", datestr[8:10])

    def test_strptime(self):
        when = pagerduty.common.strptime("1986-04-26T01:23:45+0300")
        self.assertEqual(1986, when.year)
        self.assertEqual(4, when.month)
        self.assertEqual(26, when.day)
        self.assertEqual(1, when.hour)
        self.assertEqual(23, when.minute)
        self.assertEqual(45, when.second)
        self.assertEqual("UTC+03:00", when.tzname())

    def test_successful_response(self):
        self.assertRaises(
            pagerduty.Error,
            pagerduty.successful_response,
            Response(400, json.dumps({})),
        )
        self.assertRaises(
            pagerduty.ServerHttpError,
            pagerduty.successful_response,
            Response(500, json.dumps({})),
        )

    def test_try_decoding(self):
        # Most requests, especially endpoints that follow standard patterns, will
        # respond with valid JSON:
        r = Response(
            200,
            json.dumps(
                {
                    "service": {
                        "type": "service_reference",
                        "id": "POOPBUG",
                        "summary": "A rare ID obfuscation",
                    }
                }
            ),
        )
        self.assertEqual(list(pagerduty.try_decoding(r).keys()), ["service"])
        # Deletion requests, or PUT /teams/{t_id}/users/{u_id}, will respond with an
        # empty string; json.loads will error out but try_decoding should return None:
        r = Response(204, "")
        self.assertEqual(pagerduty.try_decoding(r), None)
        # Invalid JSON:
        r = Response(
            500,
            """<html><head>
<title>500 Internal Server Error</title></head>
<body>
<h1>500 Internal Server Error</h1>
</body></html>""",
        )
        self.assertRaises(pagerduty.ServerHttpError, pagerduty.try_decoding, r)

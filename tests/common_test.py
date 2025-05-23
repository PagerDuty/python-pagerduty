import json
import unittest

from mocks import Response

import pagerduty

class SessionTest(unittest.TestCase):
    def assertDictContainsSubset(self, d0, d1):
        self.assertTrue(set(d0.keys()).issubset(set(d1.keys())),
            msg="First dict is not a subset of second dict")
        self.assertEqual(d0, dict([(k, d1[k]) for k in d0]))

class UrlHandlingTest(unittest.TestCase):

    def test_normalize_url(self):
        urls_expected = [
            (
                ('https://api.pagerduty.com/', 'users'),
                'https://api.pagerduty.com/users',
            ),
            (
                ('https://api.pagerduty.com', '/users'),
                'https://api.pagerduty.com/users',
            ),
            (
                (
                    'https://api.pagerduty.com',
                    'https://api.pagerduty.com/users',
                ),
                'https://api.pagerduty.com/users',
            )
        ]
        for (base_url_url, expected_url) in urls_expected:
            self.assertEqual(
                expected_url,
                pagerduty.normalize_url(*base_url_url)
            )
        invalid_input = [ # URL does not start with base_url
            (
                'https://api.pagerduty.com/incidents',
                'https://events.pagerduty.com/api/v2/enqueue',
            ),
            (
                'https://api.pagerduty.com/services',
                'https://some.shady-site.com/read-auth-headers',
            )
        ]
        for args in invalid_input:
            self.assertRaises(pagerduty.UrlError, pagerduty.normalize_url, *args)

class HelperFunctionsTest(unittest.TestCase):

    def test_plural_deplural(self):
        # forward
        for r_name in ('escalation_policies', 'services', 'log_entries'):
            self.assertEqual(
                r_name,
                pagerduty.plural_name(pagerduty.singular_name(r_name))
            )
        # reverse
        for o_name in ('escalation_policy', 'service', 'log_entry'):
            self.assertEqual(
                o_name,
                pagerduty.singular_name(pagerduty.plural_name(o_name))
            )

    def test_successful_response(self):
        self.assertRaises(pagerduty.Error, pagerduty.successful_response,
            Response(400, json.dumps({})))
        self.assertRaises(pagerduty.ServerHttpError, pagerduty.successful_response,
            Response(500, json.dumps({})))

    def test_try_decoding(self):
        # Most requests, especially endpoints that follow standard patterns, will
        # respond with valid JSON:
        r = Response(200, json.dumps({
            'service': {
                'type': 'service_reference',
                'id': 'POOPBUG',
                'summary': 'A rare ID obfuscation'
            }
        }))
        self.assertEqual(list(pagerduty.try_decoding(r).keys()), ['service'])
        # Deletion requests, or PUT /teams/{t_id}/users/{u_id}, will respond with an
        # empty string; json.loads will error out but try_decoding should return None:
        r = Response(204, '')
        self.assertEqual(pagerduty.try_decoding(r), None)
        # Invalid JSON:
        r = Response(500, '''<html><head>
<title>500 Internal Server Error</title></head>
<body>
<h1>500 Internal Server Error</h1>
</body></html>''')
        self.assertRaises(pagerduty.ServerHttpError, pagerduty.try_decoding, r)

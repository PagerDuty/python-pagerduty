import copy
import datetime
import json
import logging
import requests
import sys
import unittest
from datetime import timezone
from typing import Optional
from unittest.mock import Mock, MagicMock, patch, call

from common_test import SessionTest
from mocks import Response, Session

import pagerduty

def page(pagenum: int, total: int, limit: int, resource: str = 'users'):
    """
    Generate a dummy page of result data for testing classic pagination.

    This deliberately returns results 10 at a time and ignores the limit property in
    order to verify we are not using the response properties but rather the count of
    results to increment.
    :param pagenum:
        Effective page number
    :param total:
        Value of the "total" property in the response
    :param limit:
        Value of the "limit" property in the response
    """
    return json.dumps({
        resource: [{'id':i} for i in range(10*pagenum, 10*(pagenum+1))],
        'total': total,
        'more': pagenum<(total/10)-1,
        'limit': limit
    })

def page_alert_grouping_settings(after: Optional[str], limit: int) -> str:
    """
    Generate a dummy page for testing alert grouping settings API's special pagination
    """
    page = {
        # Method is agnostic to the internal schema of settings entries:
        'alert_grouping_settings': [{'foo': f"bar{i}"} for i in range(limit)],
    }
    if after is not None:
        page['after'] = after
    return json.dumps(page)

def page_analytics_raw_incident_data(limit: int, last: str, more: bool) -> str:
    """
    Generate a dummy page for testing the special pagination in the analytics API

    The test is agnostic to content and most of the response properties. It only needs
    to mock up the properties that are actually used.
    """
    body = {
        'data': [{'foo': f"bar_{i}"}  for i in range(limit)],
        'more': more
    }
    if last:
        body['last'] = last
    return json.dumps(body)

def page_cursor(wrapper, results, cursor):
    """
    Generate a dummy page of result data for testing cursor-based pagination.
    """
    return json.dumps({
        wrapper: results,
        'next_cursor': cursor
    })

class RestApiV2UrlHandlingTest(unittest.TestCase):

    def test_canonical_path(self):
        identified_urls = [
            (
                '/services/{id}',
                '/services/POOPBUG',
            ),
            (
                '/automation_actions/actions/{id}/teams/{team_id}',
                '/automation_actions/actions/PABC123/teams/PDEF456',
            ),
            (
                '/status_dashboards/url_slugs/{url_slug}/service_impacts',
                '/status_dashboards/url_slugs/my-awesome-dashboard/service_impacts',
            ),
            (
                '/{entity_type}/{id}/change_tags',
                '/services/POOPBUG/change_tags',
            ),
            ( # for https://github.com/PagerDuty/pagerduty/pull/109
                '/users/me',
                '/users/me',
            ),
        ]
        for (pattern, url) in identified_urls:
            base_url = 'https://api.pagerduty.com'
            self.assertEqual(pattern, pagerduty.canonical_path(base_url, url))

    def test_is_path_param(self):
        self.assertTrue(pagerduty.is_path_param('{id}'))
        self.assertFalse(pagerduty.is_path_param('services'))

class EntityWrappingTest(unittest.TestCase):

    def test_entity_wrappers(self):
        io_expected = [
            # Special endpoint (broken support v5.0.0 - 5.1.x) managed by script
            (('get', '/tags/{id}/users'), ('users', 'users')),
            # Conventional endpoint: singular read
            (('get', '/services/{id}'), ('service', 'service')),
            # Conventional endpoint: singular update
            (('put', '/services/{id}'), ('service', 'service')),
            # Conventional endpoint: create new
            (('pOsT', '/services'), ('service', 'service')),
            # Conventional endpoint: multi-update
            (('PUT', '/incidents/{id}/alerts'), ('alerts', 'alerts')),
            # Conventional endpoint: list resources
            (('get', '/incidents/{id}/alerts'), ('alerts', 'alerts')),
            # Expanded endpoint support: different request/response wrappers
            (('put', '/incidents/{id}/merge'), ('source_incidents', 'incident')),
            # Expanded support: same wrapper for req/res and all methods
            (
                ('post', '/event_orchestrations'),
                ('orchestrations', 'orchestrations')
            ),
            (
                ('get', '/event_orchestrations'),
                ('orchestrations', 'orchestrations')
            ),
            # Disabled
            (('post', '/analytics/raw/incidents'), (None, None)),
        ]
        for ((method, path), rval) in io_expected:
            self.assertEqual(rval, pagerduty.entity_wrappers(method, path))

    def test_infer_entity_wrapper(self):
        io_expected = [
            (('get', '/users'), 'users'),
            (('PoSt', '/users'), 'user'),
            (('PUT', '/service/{id}'), 'service'),
            (('PUT', '/incidents/{id}/alerts'), 'alerts'),
        ]
        for (method_path, expected_wrapper) in io_expected:
            self.assertEqual(
                expected_wrapper,
                pagerduty.infer_entity_wrapper(*method_path),
            )

    def test_unwrap(self):
        # Response has unexpected type, raise:
        r = Response(200, json.dumps([]))
        self.assertRaises(pagerduty.ServerHttpError, pagerduty.unwrap, r, 'foo')
        # Response has unexpected structure, raise:
        r = Response(200, json.dumps({'foo_1': {'bar':1}, 'foo_2': 'bar2'}))
        self.assertRaises(pagerduty.ServerHttpError, pagerduty.unwrap, r, 'foo')
        # Response has the expected structure, return the wrapped entity:
        foo_entity = {'type':'foo_reference', 'id': 'PFOOBAR'}
        r = Response(200, json.dumps({'foo': foo_entity}))
        self.assertEqual(foo_entity, pagerduty.unwrap(r, 'foo'))
        # Disabled entity wrapping (wrapper=None), return body as-is
        self.assertEqual({'foo': foo_entity}, pagerduty.unwrap(r, None))

class FunctionDecoratorsTest(unittest.TestCase):
    @patch.object(pagerduty.RestApiV2Client, 'put')
    def test_resource_path(self, put_method):
        sess = pagerduty.RestApiV2Client('some-key')
        resource_url = 'https://api.pagerduty.com/users/PSOMEUSR'
        user = {
            'id': 'PSOMEUSR',
            'type': 'user',
            'self': resource_url,
            'name': 'User McUserson',
            'email': 'user@organization.com'
        }
        put_method.return_value = Response(200, json.dumps({'user': user}),
            method='PUT', url=resource_url)
        sess.rput(user, json=user)
        put_method.assert_called_with(resource_url, json={'user': user})

    def test_wrapped_entities(self):
        do_http_things = MagicMock()
        response = MagicMock()
        do_http_things.return_value = response
        session = pagerduty.RestApiV2Client('some_key')
        dummy_session = MagicMock()
        def reset_mocks():
            do_http_things.reset_mock()
            response.reset_mock()
            do_http_things.return_value = response
            dummy_session.reset_mock()

        # OK response, good JSON: JSON-decode and unpack response
        response.ok = True
        response.json.return_value = {'service': {'name': 'value'}}
        do_http_things.__name__ = 'rput' # just for instance
        self.assertEqual(
            pagerduty.wrapped_entities(do_http_things)(session,
                '/services/PTHINGY'),
            {'name': 'value'}
        )
        reset_mocks()

        # OK response, bad JSON: raise exception.
        response.ok = True
        do_http_things.__name__ = 'rput' # just for instance
        response.json.side_effect = [ValueError('Bad JSON!')]
        self.assertRaises(pagerduty.Error,
            pagerduty.wrapped_entities(do_http_things), session, '/services')
        reset_mocks()

        # OK response, but the response isn't what we expected: exception.
        do_http_things.reset_mock()
        response.reset_mock()
        response.json = MagicMock()
        response.ok = True
        do_http_things.return_value = response
        do_http_things.__name__ = 'rput' # just for instance
        response.json.return_value = {'nope': 'nopenope'}
        self.assertRaises(pagerduty.HttpError,
            pagerduty.wrapped_entities(do_http_things), session, '/services')
        reset_mocks()

        # Not OK response, raise
        response.reset_mock()
        response.ok = False
        do_http_things.__name__ = 'rput' # just for instance
        self.assertRaises(pagerduty.Error,
            pagerduty.wrapped_entities(do_http_things), session, '/services')
        reset_mocks()

        # GET /<index>: use a different envelope name
        response.ok = True
        users_array = [{"type":"user","email":"user@example.com",
            "summary":"User McUserson"}]
        response.json.return_value = {'users': users_array}
        do_http_things.__name__ = 'rget'
        dummy_session.url = 'https://api.pagerduty.com'
        dummy_session.canonical_path.return_value = '/users'
        dummy_session.entity_wrappers.return_value = ('users', 'users')
        self.assertEqual(users_array,
            pagerduty.wrapped_entities(do_http_things)(dummy_session, '/users',
                query='user'))
        reset_mocks()

        # Test request body JSON envelope stuff in post/put
        # Response body validation
        do_http_things.__name__ = 'rpost'
        user_payload = {'email':'user@example.com', 'name':'User McUserson'}
        dummy_session.url = 'https://api.pagerduty.com'
        dummy_session.canonical_path.return_value = '/users'
        dummy_session.entity_wrappers.return_value = ('user', 'user')
        self.assertRaises(
            pagerduty.Error,
            pagerduty.wrapped_entities(do_http_things),
            dummy_session, '/users', json=user_payload
        )
        reset_mocks()
        # Add type property; should work now and automatically pack the user
        # object into a JSON object inside the envelope.
        user_payload['type'] = 'user'
        dummy_session.url = 'https://api.pagerduty.com'
        dummy_session.canonical_path.return_value = '/users'
        do_http_things.__name__ = 'rpost'
        response.ok = True
        created_user = user_payload.copy()
        created_user['id'] = 'P456XYZ'
        response.json.return_value = {'user':created_user}
        self.assertEqual(
            created_user,
            pagerduty.wrapped_entities(do_http_things)(dummy_session, '/users',
                json=user_payload)
        )
        do_http_things.assert_called_with(dummy_session, '/users',
            json={'user':user_payload})

        reset_mocks()
        # Test auto-envelope functionality for multi-update
        incidents = [{'id':'PABC123'}, {'id':'PDEF456'}]
        dummy_session.url = 'https://api.pagerduty.com'
        dummy_session.canonical_path.return_value = '/incidents'
        dummy_session.entity_wrappers.return_value = ('incidents', 'incidents')
        do_http_things.__name__ = 'rput'
        response.ok = True
        updated_incidents = copy.deepcopy(incidents)
        response.json.return_value = {'incidents': updated_incidents}
        self.assertEqual(
            updated_incidents,
            pagerduty.wrapped_entities(do_http_things)(dummy_session,
                '/incidents', json=incidents)
        )
        # The final value of the json parameter passed to the method (which goes
        # straight to put) should be the plural resource name
        self.assertEqual(
            do_http_things.mock_calls[0][2]['json'],
            {'incidents': incidents}
        )

class RestApiV2ClientTest(SessionTest):

    def test_oauth_headers(self):
        oauth_token = 'randomly generated lol'
        sess = pagerduty.RestApiV2Client(oauth_token, 'oauth2')
        self.assertEqual(
            sess.auth_header["Authorization"],
            "Bearer "+ oauth_token
        )

    def test_print_debug(self):
        sess = pagerduty.RestApiV2Client('token')
        log = Mock()
        log.setLevel = Mock()
        log.addHandler = Mock()
        sess.log = log
        # Enable:
        sess.print_debug = True
        log.setLevel.assert_called_once_with(logging.DEBUG)
        self.assertEqual(1, len(log.addHandler.call_args_list))
        self.assertTrue(isinstance(
            log.addHandler.call_args_list[0][0][0],
            logging.StreamHandler
        ))
        # Disable:
        log.setLevel.reset_mock()
        log.removeHandler = Mock()
        sess.print_debug = False
        log.setLevel.assert_called_once_with(logging.NOTSET)
        self.assertEqual(1, len(log.removeHandler.call_args_list))
        self.assertTrue(isinstance(
            log.removeHandler.call_args_list[0][0][0],
            logging.StreamHandler
        ))
        # Setter called via constructor:
        sess = pagerduty.RestApiV2Client('token', debug=True)
        self.assertTrue(isinstance(sess._debugHandler, logging.StreamHandler))
        # Setter should be idempotent:
        sess.print_debug = False
        sess.print_debug = False
        self.assertFalse(hasattr(sess, '_debugHandler'))
        sess.print_debug = True
        sess.print_debug = True
        self.assertTrue(hasattr(sess, '_debugHandler'))

    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    def test_find(self, iter_all):
        sess = pagerduty.RestApiV2Client('token')
        iter_all.return_value = iter([
            {'type':'user', 'name': 'Someone Else', 'email':'some1@me.me.me', 'f':1},
            {'type':'user', 'name': 'Space Person', 'email':'some1@me.me ', 'f':2},
            {'type':'user', 'name': 'Someone Personson', 'email':'some1@me.me', 'f':3},
            {'type':'user', 'name': 'Numeric Fields', 'email': 'test@example.com', 'f':5}
        ])
        self.assertEqual(
            'Someone Personson',
            sess.find('users', 'some1@me.me', attribute='email')['name']
        )
        iter_all.assert_called_with('users', params={'query':'some1@me.me'})
        self.assertEqual(
            'Numeric Fields',
            sess.find('users', 5, attribute='f')['name']
        )

    @patch.object(pagerduty.RestApiV2Client, 'get')
    def test_get_total_valid(self, get):
        """
        Test RestApiV2Client.get_total for a valid response
        """
        count = 500
        pd_start = '2010-01-01T00:00:00Z'
        now = pagerduty.common.strftime(datetime.datetime.now(timezone.utc))
        get.return_value = Response(200, json.dumps({
            'total': count,
            # Don't care about content, just the total property
            'log_entries': {}
        }))
        client = pagerduty.RestApiV2Client('token')
        total = client.get_total('/log_entries', params = {
            'since': pd_start,
            'until': now
        })
        self.assertEqual(total, count)
        get.assert_called_once_with(
            '/log_entries',
            params = {
                'since': pd_start,
                'until': now,
                'total': True,
                'limit': 1,
                'offset': 0
            }
        )

    @patch.object(pagerduty.RestApiV2Client, 'get')
    def test_get_total_invalid(self, get):
        """
        Test RestApiV2Client.get_total for a response that lacks "total"
        """
        get.return_value = Response(200, json.dumps({
            'log_entries': {}
        }))
        pd_start = '2010-01-01T00:00:00Z'
        now = pagerduty.common.strftime(datetime.datetime.now(timezone.utc))
        get.return_value = Response(200, json.dumps({
            'widgets': {}
        }))
        client = pagerduty.RestApiV2Client('token')
        self.assertRaises(
            pagerduty.ServerHttpError,
            client.get_total,
            '/log_entries',
            params = {
                'since': pd_start,
                'until': now
            }
        )

    @patch.object(pagerduty.RestApiV2Client, 'get')
    def test_iter_alert_grouping_settings(self, get):
        """
        Test the special pagination style of the alert grouping settings API.
        """
        AFTER_1 = 'abcd1234'
        AFTER_2 = 'defg5678'
        client = pagerduty.RestApiV2Client('token')
        get.side_effect = [
            Response(200, page_alert_grouping_settings(AFTER_1, 2)),
            Response(200, page_alert_grouping_settings(AFTER_2, 2)),
            Response(200, page_alert_grouping_settings(None, 2))
        ]
        data = list(client.iter_alert_grouping_settings())
        self.assertEqual(6, len(data))
        self.assertEqual(3, get.call_count)
        # A page's "after" cursor is the value of "after" from the page before it:
        self.assertEqual(
            AFTER_1,
            get.call_args_list[1][1]['params']['after']
        )

    @patch.object(pagerduty.RestApiV2Client, 'iter_cursor')
    @patch.object(pagerduty.RestApiV2Client, 'get')
    def test_iter_all(self, get, iter_cursor):
        sess = pagerduty.RestApiV2Client('token')
        sess.log = MagicMock()

        # Test: user uses iter_all on an endpoint that supports cursor-based
        # pagination, short-circuit to iter_cursor
        path = '/audit/records'
        cpath = pagerduty.canonical_path('https://api.pagerduty.com', path)
        self.assertTrue(
            cpath in pagerduty.rest_api_v2_client.CURSOR_BASED_PAGINATION_PATHS
        )
        iter_cursor.return_value = []
        passed_kw = {
            'params': {
                "since": "2025-01-01T00:00:00Z",
                "until": "2025-05-19T00:00:00Z"
            },
            'item_hook': lambda x, y, z: print(f"{x}: {y}/{z}"),
            'page_size': 42
        }
        self.assertEqual([], list(sess.iter_all('/audit/records', **passed_kw)))
        iter_cursor.assert_called_once_with('/audit/records', **passed_kw)

        # Test: user tries to use iter_all on a singular resource, raise error:
        self.assertRaises(
            pagerduty.UrlError,
            lambda p: list(sess.iter_all(p)),
            'users/PABC123'
        )
        # Test: user tries to use iter_all on an endpoint that doesn't actually
        # support pagination, raise error:
        self.assertRaises(
            pagerduty.UrlError,
            lambda p: list(sess.iter_all(p)),
            '/analytics/raw/incidents/Q3R8ZN19Z8K083/responses'
        )
        iter_param = lambda p: json.dumps({
            'limit':10, 'total': True, 'offset': 0
        })
        get.side_effect = [
            Response(200, page(0, 30, 10)),
            Response(200, page(1, 30, 10)),
            Response(200, page(2, 30, 10)),
        ]
        # Follow-up to #103: add more odd parameters to the URL
        weirdurl='https://api.pagerduty.com/users?number=1&filters[]=foo'
        hook = MagicMock()
        items = list(sess.iter_all(weirdurl, item_hook=hook, total=True, page_size=10))
        self.assertEqual(3, get.call_count)
        self.assertEqual(30, len(items))
        get.assert_has_calls(
            [
                call(weirdurl, params={'limit':10, 'total':1, 'offset':0}),
                call(weirdurl, params={'limit':10, 'total':1, 'offset':10}),
                call(weirdurl, params={'limit':10, 'total':1, 'offset':20}),
            ],
        )
        hook.assert_any_call({'id':14}, 15, 30)

        # Test stopping iteration on non-success status
        get.reset_mock()
        error_encountered = [
            Response(200, page(0, 50, 10)),
            Response(200, page(1, 50, 10)),
            Response(200, page(2, 50, 10)),
            Response(400, page(3, 50, 10)), # break
            Response(200, page(4, 50, 10)),
        ]
        get.side_effect = copy.deepcopy(error_encountered)
        self.assertRaises(pagerduty.Error, list, sess.iter_all(weirdurl))

        # Test reaching the iteration limit:
        get.reset_mock()
        bigiter = sess.iter_all('log_entries', page_size=100,
            params={'offset': '9901'})
        self.assertRaises(StopIteration, next, bigiter)

        # Test (temporary, until underlying issue in the API is resolved) using
        # the result count to increment offset instead of `limit` reported in
        # API response
        get.reset_mock()
        iter_param = lambda p: json.dumps({
            'limit':10, 'total': True, 'offset': 0
        })
        get.side_effect = [
            Response(200, page(0, 30, None)),
            Response(200, page(1, 30, 42)),
            Response(200, page(2, 30, 2020)),
        ]
        weirdurl='https://api.pagerduty.com/users?number=1'
        hook = MagicMock()
        items = list(sess.iter_all(weirdurl, item_hook=hook, total=True, page_size=10))
        self.assertEqual(30, len(items))

    @patch.object(pagerduty.RestApiV2Client, 'post')
    def test_iter_analytics_raw_incidents(self, post):
        LIMIT = 10
        client = pagerduty.RestApiV2Client('token')
        # Test: exit if "more" indicates the end of the data set, use custom limit
        LAST_1 = 'abcd1234'
        LAST_2 = 'defg5678'
        post.side_effect = [
            Response(200, page_analytics_raw_incident_data(LIMIT, LAST_1, True)),
            Response(200, page_analytics_raw_incident_data(LIMIT, LAST_2, False))
        ]
        data = list(client.iter_analytics_raw_incidents({'bar': 'baz'}, limit=LIMIT))
        self.assertEqual(LIMIT*2, len(data))
        self.assertEqual(2, post.call_count)
        self.assertEqual(
            LAST_1,
            post.call_args_list[1][1]['json']['starting_after']
        )
        # Test: exit if the "last" property is not set, use default limit
        post.reset_mock()
        post.side_effect = [
            Response(200, page_analytics_raw_incident_data(LIMIT, None, True)),
            Response(200, page_analytics_raw_incident_data(LIMIT, None, True))
        ]
        data = list(client.iter_analytics_raw_incidents({'bar': 'baz'}))
        self.assertEqual(1, post.call_count)
        self.assertEqual(
            client.default_page_size,
            post.call_args_list[0][1]['json']['limit']
        )

    @patch.object(pagerduty.RestApiV2Client, 'get')
    def test_iter_cursor(self, get):
        sess = pagerduty.RestApiV2Client('token')
        sess.log = MagicMock()
        # Test: user tries to use iter_cursor where it won't work, raise:
        self.assertRaises(
            pagerduty.UrlError,
            lambda p: list(sess.iter_cursor(p)),
            'incidents', # Maybe some glorious day, but not as of this writing
        )

        # Test: cursor parameter exchange, stop iteration when records run out,
        # etc. This isn't what the schema of the audit records API actually
        # looks like apart from the entity wrapper, but that doesn't matter for
        # the purpose of this test.
        get.side_effect = [
            Response(200, page_cursor('records', [1, 2, 3], 2)),
            Response(200, page_cursor('records', [4, 5, 6], 5)),
            Response(200, page_cursor('records', [7, 8, 9], None))
        ]
        self.assertEqual(
            list(sess.iter_cursor('/audit/records')),
            list(range(1,10))
        )
        # It should send the next_cursor body parameter from the second to
        # last response as the cursor query parameter in the final request
        self.assertEqual(get.mock_calls[-1][2]['params']['cursor'], 5)

    # iter_history tests
    #
    # Each call to iter_history will result in a "total" request (limit=1, offset=0)
    # followed by iter_all sub-requests (if done recursing) for each interval, or a
    # series of recursive calls to iter_history. The test data here don't reflect
    # anything realistic, especially because the total number of records changes
    # depending on the level of recursion, but the stubbing/mocking return values are
    # just to test that the logic works.

    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    @patch.object(pagerduty.RestApiV2Client, 'get_total')
    def test_iter_history_recursion_1s(self, get_total, iter_all):
        """
        Test iter_history stop-iteration on hitting the minimum interval length
        """
        client = pagerduty.RestApiV2Client('token')
        # Checks for "total" in each sub-interval: the first for the whole 2s, the
        # second for the first 1-second sub-interval and the third for the second.
        get_total.side_effect = [
            # Top level: total is over the limit; bisect
            pagerduty.ITERATION_LIMIT+2,
            # Level 1, sub-interval 1: call iter_all; max total not exceeded
            1,
            # Level 1, sub-interval 2: call iter_all; max total exceeded but interval=1s
            pagerduty.ITERATION_LIMIT+1
        ]
        iter_all.side_effect = [
            iter([{'type': 'log_entry'}]),
            iter([{'type': 'log_entry'}])
        ]

        now = datetime.datetime.now(timezone.utc)
        future3 = now + datetime.timedelta(seconds=2)
        results = list(client.iter_history('/log_entries', now, future3))
        self.assertEqual(2, len(iter_all.mock_calls))
        self.assertEqual([{'type': 'log_entry'}]*2, results)

    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    @patch.object(pagerduty.RestApiV2Client, 'get_total')
    def test_iter_history_recursion_limit(self, get_total, iter_all):
        """
        Test iter_history stop-iteration on hitting the recursion depth limit
        """
        # Adjust the recursion limit so we only need 1 level of stub data:
        client = pagerduty.RestApiV2Client('token')
        original_recursion_limit = pagerduty.rest_api_v2_client.RECURSION_LIMIT
        pagerduty.rest_api_v2_client.RECURSION_LIMIT = 1
        # Checks for "total" in each sub-interval: The expected breakdown of 3s is a 1s
        # interval followed by a 2s interval at the first level of recursion, and then
        # two 1s intervals.
        get_total.side_effect = [
            # Top level: total is over the limit; bisect
            pagerduty.ITERATION_LIMIT+2,
            # Level 1, sub-interval 1: call iter_all; max total not exceeded
            1,
            # Level 1, sub-interval 2: call iter_all; max recursion depth reached
            pagerduty.ITERATION_LIMIT+1
        ]
        iter_all.side_effect = [
            iter([{'type': 'log_entry'}]),
            iter([{'type': 'log_entry'}])
        ]
        now = datetime.datetime.now(timezone.utc)
        future6 = now + datetime.timedelta(seconds=6)
        results = list(client.iter_history('/log_entries', now, future6))
        self.assertEqual([{'type': 'log_entry'}]*2, results)
        self.assertEqual(2, len(iter_all.mock_calls))
        pagerduty.rest_api_v2_client.RECURSION_LIMIT = original_recursion_limit

    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    @patch.object(pagerduty.RestApiV2Client, 'get_total')
    @patch.object(pagerduty.RestApiV2Client, 'iter_cursor')
    def test_iter_history_cursor_callout(self, iter_cursor, get_total,
                iter_all):
        """
        Validate the method defers to iter_cursor when used with cursor-based pagination
        """
        client = pagerduty.RestApiV2Client('token')
        now = datetime.datetime.now(timezone.utc)
        future6 = now + datetime.timedelta(seconds=6)
        iter_cursor.side_effect = [
            iter([{'type': 'record'}])
        ]
        deletions = list(client.iter_history('/audit/records', now, future6, params={
            'actions': ['delete']
        }))
        iter_all.assert_not_called()
        get_total.assert_not_called()
        iter_cursor.assert_called_once()
        self.assertEqual('/audit/records', iter_cursor.mock_calls[0][1][0])
        self.assertEqual(
            ['delete'],
            iter_cursor.mock_calls[0][2]['params']['actions']
        )

    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    def test_iter_incident_notes_single_incident(self, iter_all):
        """
        Validate proper function when requesting incident notes for a given incident ID
        """
        INCIDENT_ID = 'Q789GHI'
        iter_all.return_value = iter([
            {'type': 'trigger_log_entry', 'summary': 'server on fire'},
            {'type': 'annotate_log_entry', 'summary': 'used extinguisher'},
            {'type': 'annotate_log_entry', 'summary': 'will not reboot, replacing.'},
            {'type': 'resolve_log_entry'}
        ])
        client = pagerduty.RestApiV2Client('token')

        notes = list(client.iter_incident_notes(incident_id = INCIDENT_ID, params = {
            'team_ids[]': ['Q1GN0R3M3']
        }))
        self.assertEqual(2, len(notes))
        self.assertEqual(
            f"/incidents/{INCIDENT_ID}/log_entries",
            iter_all.call_args[0][0]
        )
        params = iter_all.call_args_list[0][1]['params']
        self.assertFalse('team_ids'   in params)
        self.assertFalse('team_ids[]' in params)

    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    def test_iter_incident_notes_teams_filter(self, iter_all):
        """
        Validate proper function when requesting incident notes for specified teams
        """
        TEAM_ID_1 = 'QABCDE12345'
        TEAM_ID_2 = 'QFGHIJ67890'
        iter_all.return_value = iter([
            {'type': 'trigger_log_entry', 'summary': 'server on fire'},
            {'type': 'annotate_log_entry', 'summary': 'used extinguisher'},
            {'type': 'annotate_log_entry', 'summary': 'will not reboot, replacing.'},
            {'type': 'resolve_log_entry'}
        ])
        client = pagerduty.RestApiV2Client('token')
        notes = list(client.iter_incident_notes(params = {
            'team_ids[]': [TEAM_ID_1, TEAM_ID_2]
        }))
        self.assertEqual(2, len(notes))
        self.assertEqual(
            '/log_entries',
            iter_all.call_args[0][0]
        )
        params = iter_all.call_args_list[0][1]['params']
        self.assertTrue('team_ids[]' in params)
        self.assertEqual([TEAM_ID_1, TEAM_ID_2], params['team_ids[]'])

    @patch.object(pagerduty.RestApiV2Client, 'rput')
    @patch.object(pagerduty.RestApiV2Client, 'rpost')
    @patch.object(pagerduty.RestApiV2Client, 'iter_all')
    def test_persist(self, iterator, creator, updater):
        user = {
            "name": "User McUserson",
            "email": "user@organization.com",
            "type": "user"
        }
        # Do not create if the user exists already (default)
        iterator.return_value = iter([user])
        sess = pagerduty.RestApiV2Client('apiKey')
        sess.persist('users', 'email', user)
        creator.assert_not_called()
        # Call session.rpost to create if the user does not exist
        iterator.return_value = iter([])
        sess.persist('users', 'email', user)
        creator.assert_called_with('users', json=user)
        # Call session.rput to update an existing user if update is True
        iterator.return_value = iter([user])
        new_user = dict(user)
        new_user.update({
            'job_title': 'Testing the app',
            'self': 'https://api.pagerduty.com/users/PCWKOPZ'
        })
        sess.persist('users', 'email', new_user, update=True)
        updater.assert_called_with(new_user, json=new_user)
        # Call session.rput to update but w/no change so no API PUT request:
        updater.reset_mock()
        existing_user = dict(new_user)
        iterator.return_value = iter([existing_user])
        sess.persist('users', 'email', new_user, update=True)
        updater.assert_not_called()

    def test_postprocess(self):
        logger = MagicMock()

        # Test call count and API time
        response = Response(201, json.dumps({'key':'value'}), method='POST',
            url='https://api.pagerduty.com/users/PCWKOPZ/contact_methods')
        sess = pagerduty.RestApiV2Client('apikey')
        sess.postprocess(response)

        self.assertEqual(
            1,
            sess.api_call_counts['POST /users/{id}/contact_methods']
        )
        self.assertEqual(
            1.5,
            sess.api_time['POST /users/{id}/contact_methods']
        )
        response = Response(200, json.dumps({'key':'value'}), method='GET',
            url='https://api.pagerduty.com/users/PCWKOPZ')
        sess.postprocess(response)
        self.assertEqual(1, sess.api_call_counts['GET /users/{id}'])
        self.assertEqual(1.5, sess.api_time['GET /users/{id}'])

        # Test logging
        response = Response(500, json.dumps({'key': 'value'}), method='GET',
            url='https://api.pagerduty.com/users/PCWKOPZ/contact_methods')
        sess = pagerduty.RestApiV2Client('apikey')
        sess.log = logger
        sess.postprocess(response)
        if not (sys.version_info.major == 3 and sys.version_info.minor == 5):
            # These assertion methods are not available in Python 3.5
            logger.error.assert_called_once()
            logger.debug.assert_called_once()
        # Make sure we have correct logging params / number of params:
        logger.error.call_args[0][0]%logger.error.call_args[0][1:]
        logger.debug.call_args[0][0]%logger.debug.call_args[0][1:]


    @patch.object(pagerduty.RestApiV2Client, 'postprocess')
    def test_request(self, postprocess):
        sess = pagerduty.RestApiV2Client('12345')
        parent = Session()
        request = MagicMock()
        # Expected headers:
        headers_get = {
            'Accept': 'application/vnd.pagerduty+json;version=2',
            'Authorization': 'Token token=12345',
            'User-Agent': 'python-pagerduty/%s python-requests/%s Python/%d.%d'%(
                pagerduty.__version__,
                requests.__version__,
                sys.version_info.major,
                sys.version_info.minor
            ),
        }
        # Check default headers:
        self.assertDictContainsSubset(headers_get, sess.prepare_headers('GET'))
        headers_get.update(sess.prepare_headers('GET'))
        # When submitting post/put, the content type should also be set
        headers_post = headers_get.copy()
        headers_post.update({'Content-Type': 'application/json'})
        parent.headers = headers_get

        with patch.object(sess, 'parent', new=parent):
            parent.request = request
            # Test bad request method
            self.assertRaises(
                pagerduty.Error,
                sess.request,
                *['poke', '/something']
            )
            request.assert_not_called()
            # Dummy user
            user = {
                "name": "User McUserson",
                "type": "user",
                "role": "limited_user",
                "email": "user@example.com",
            }
            users = {'users': user}

            # Test basic GET & profiling
            request.return_value = Response(200, json.dumps(users))
            r = sess.request('get', '/users')
            postprocess.assert_called_with(request.return_value)
            headers = headers_get.copy()
            request.assert_called_once_with('GET',
                'https://api.pagerduty.com/users', headers=headers_get,
                stream=False, timeout=pagerduty.TIMEOUT)
            request.reset_mock()

            # Test POST/PUT (in terms of code coverage they're identical)
            request.return_value = Response(201, json.dumps({'user': user}))
            sess.request('post', 'users', json={'user':user})
            request.assert_called_once_with(
                'POST', 'https://api.pagerduty.com/users',
                headers=headers_post, json={'user':user}, stream=False, timeout=pagerduty.TIMEOUT)
            request.reset_mock()

            # Test GET with parameters and using a HTTP verb method
            request.return_value = Response(200, json.dumps({'users': [user]}))
            user_query = {'query': 'user@example.com'}
            r = sess.get('/users', params=user_query)
            request.assert_called_once_with(
                'GET', 'https://api.pagerduty.com/users',
                headers=headers_get, params=user_query, stream=False,
                allow_redirects=True, timeout=pagerduty.TIMEOUT)
            request.reset_mock()

            # Test GET with one array-type parameter not suffixed with []
            request.return_value = Response(200, json.dumps({'users': [user]}))
            user_query = {'query': 'user@example.com', 'team_ids':['PCWKOPZ']}
            modified_user_query = copy.deepcopy(user_query)
            modified_user_query['team_ids[]'] = user_query['team_ids']
            del(modified_user_query['team_ids'])
            r = sess.get('/users', params=user_query)
            request.assert_called_once_with(
                'GET', 'https://api.pagerduty.com/users',
                headers=headers_get, params=modified_user_query, stream=False,
                allow_redirects=True, timeout=pagerduty.TIMEOUT)
            request.reset_mock()

            # Test a POST request with additional headers
            request.return_value = Response(201, json.dumps({'user': user}),
                method='POST')
            headers_special = headers_post.copy()
            headers_special.update({"X-Tra-Special-Header": "1"})
            r = sess.post('/users/PD6LYSO/future_endpoint',
                headers=headers_special, json={'user':user})
            request.assert_called_once_with('POST',
                'https://api.pagerduty.com/users/PD6LYSO/future_endpoint',
                headers=headers_special, json={'user': user}, stream=False,
                data=None, timeout=pagerduty.TIMEOUT)
            request.reset_mock()

            # Test hitting the rate limit
            request.side_effect = [
                Response(429, json.dumps({'error': {'message': 'chill out'}})),
                Response(429, json.dumps({'error': {'message': 'chill out'}})),
                Response(200, json.dumps({'user': user})),
            ]
            with patch.object(pagerduty.api_client.time, 'sleep') as sleep:
                r = sess.get('/users')
                self.assertTrue(r.ok) # should only return after success
                self.assertEqual(3, request.call_count)
                self.assertEqual(2, sleep.call_count)
            request.reset_mock()
            request.side_effect = None

            # Test a 401 (should raise Exception)
            request.return_value = Response(401, json.dumps({
                'error': {
                    'code': 2006,
                    'message': "You shall not pass.",
                }
            }))
            self.assertRaises(pagerduty.Error, sess.request, 'get',
                '/services')
            request.reset_mock()

            # Test retry logic:
            with patch.object(pagerduty.api_client.time, 'sleep') as sleep:
                # Test getting a connection error and succeeding the final time.
                returns = [
                    pagerduty.api_client.Urllib3HttpError("D'oh!")
                ]*sess.max_network_attempts
                returns.append(Response(200, json.dumps({'user': user})))
                request.side_effect = returns
                with patch.object(sess, 'cooldown_factor') as cdf:
                    cdf.return_value = 2.0
                    r = sess.get('/users/P123456')
                    self.assertEqual(sess.max_network_attempts+1,
                        request.call_count)
                    self.assertEqual(sess.max_network_attempts, sleep.call_count)
                    self.assertEqual(sess.max_network_attempts, cdf.call_count)
                    self.assertTrue(r.ok)
                request.reset_mock()
                sleep.reset_mock()

                # Now test handling a non-transient error when the client
                # library itself hits odd issues that it can't handle, i.e.
                # network, and that the raised exception includes context:
                raises = [pagerduty.api_client.RequestException("D'oh!")]*(
                    sess.max_network_attempts+1)
                request.side_effect = raises
                try:
                    sess.get('/users')
                    self.assertTrue(False, msg='Exception not raised after ' \
                        'retry maximum count reached')
                except pagerduty.Error as e:
                    self.assertEqual(e.__cause__, raises[-1])
                except Exception as e:
                    self.assertTrue(False, msg='Raised exception not of the ' \
                        f"expected class; was {e.__class__}")
                self.assertEqual(sess.max_network_attempts+1,
                    request.call_count)
                self.assertEqual(sess.max_network_attempts, sleep.call_count)

                # Test custom retry logic:
                sess.retry[404] = 3
                request.side_effect = [
                    Response(404, json.dumps({})),
                    Response(404, json.dumps({})),
                    Response(200, json.dumps({'user': user})),
                ]
                with patch.object(sess, 'cooldown_factor') as cdf:
                    cdf.return_value = 2.0
                    r = sess.get('/users/P123456')
                    self.assertEqual(200, r.status_code)
                    self.assertEqual(2, cdf.call_count)
                # Test retry logic with too many 404s
                sess.retry[404] = 1
                request.side_effect = [
                    Response(404, json.dumps({})),
                    Response(404, json.dumps({})),
                    Response(200, json.dumps({'user': user})),
                ]
                sess.log = MagicMock()
                r = sess.get('/users/P123456')
                self.assertEqual(404, r.status_code)

    @patch.object(pagerduty.RestApiV2Client, 'get')
    def test_rget(self, get):
        response200 = Response(200, '{"user":{"type":"user_reference",'
            '"email":"user@example.com","summary":"User McUserson"}}')
        get.return_value = response200
        s = pagerduty.RestApiV2Client('token')
        self.assertEqual(
            {"type":"user_reference","email":"user@example.com",
                "summary":"User McUserson"},
            s.rget('/users/P123ABC'))
        # This is (forcefully) valid JSON but no matter; it should raise
        # PDClientErorr nonetheless
        response404 = Response(404, '{"user": {"email": "user@example.com"}}')
        get.reset_mock()
        get.return_value = response404
        self.assertRaises(pagerduty.Error, s.rget, '/users/P123ABC')

    @patch.object(pagerduty.RestApiV2Client, 'rget')
    def test_subdomain(self, rget):
        rget.return_value = [{'html_url': 'https://something.pagerduty.com'}]
        sess = pagerduty.RestApiV2Client('key')
        self.assertEqual('something', sess.subdomain)
        self.assertEqual('something', sess.subdomain)
        rget.assert_called_once_with('users', params={'limit':1})

    def test_truncated_key(self):
        sess = pagerduty.RestApiV2Client('abc1234', 'token')
        self.assertEqual('*1234', sess.trunc_key)

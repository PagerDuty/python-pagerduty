import copy
import datetime
import json
import logging
import httpx
import sys
import unittest
from datetime import timezone
from typing import Optional
from unittest.mock import Mock, MagicMock, patch, call

import pagerduty
import pagerduty.rest_api_v2_base_client
from common_test import ClientTest, Client, Response
from pagerduty.rest_api_v2_client import CANONICAL_PATHS

def page(pagenum: int, total: int, limit: int, resource: str = "users"):
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
    return json.dumps(
        {
            resource: [
                {"id": i} for i in range(10 * pagenum, 10 * (pagenum + 1))
            ],
            "total": total,
            "more": pagenum < (total / 10) - 1,
            "limit": limit,
        }
    )

def page_cursor(wrapper, results, cursor):
    """
    Generate a dummy page of result data for testing cursor-based pagination.
    """
    return json.dumps({wrapper: results, "next_cursor": cursor})


class RestApiV2UrlHandlingTest(ClientTest):
    def test_canonical_path(self):
        identified_urls = [
            (
                "/services/{id}",
                "/services/POOPBUG",
            ),
            (
                "/automation_actions/actions/{id}/teams/{team_id}",
                "/automation_actions/actions/PABC123/teams/PDEF456",
            ),
            (
                "/status_dashboards/url_slugs/{url_slug}/service_impacts",
                "/status_dashboards/url_slugs/my-awesome-dashboard/service_impacts",
            ),
            (
                "/{entity_type}/{id}/change_tags",
                "/services/POOPBUG/change_tags",
            ),
            (  # for https://github.com/PagerDuty/pagerduty/pull/109
                "/users/me",
                "/users/me",
            ),
        ]
        for pattern, url in identified_urls:
            base_url = "https://api.pagerduty.com"
            self.assertEqual(
                pattern,
                pagerduty.rest_api_v2_base_client.canonical_path(
                    CANONICAL_PATHS,
                    base_url,
                    url
                )
            )
            # TODO (issue 73): remove this wrapper; for now we support with
            # testing both the wrapper and the generic method:
            self.assertEqual(pattern, pagerduty.canonical_path(base_url, url))

    def test_is_path_param(self):
        self.assertTrue(pagerduty.is_path_param("{id}"))
        self.assertFalse(pagerduty.is_path_param("services"))


class EntityWrappingTest(unittest.TestCase):
    def test_entity_wrappers(self):
        io_expected = [
            # Special endpoint (broken support v5.0.0 - 5.1.x) managed by script
            (("get", "/tags/{id}/users"), ("users", "users")),
            # Conventional endpoint: singular read
            (("get", "/services/{id}"), ("service", "service")),
            # Conventional endpoint: singular update
            (("put", "/services/{id}"), ("service", "service")),
            # Conventional endpoint: create new
            (("pOsT", "/services"), ("service", "service")),
            # Conventional endpoint: multi-update
            (("PUT", "/incidents/{id}/alerts"), ("alerts", "alerts")),
            # Conventional endpoint: list resources
            (("get", "/incidents/{id}/alerts"), ("alerts", "alerts")),
            # Expanded endpoint support: different request/response wrappers
            (
                ("put", "/incidents/{id}/merge"),
                ("source_incidents", "incident"),
            ),
            # Expanded support: same wrapper for req/res and all methods
            (
                ("post", "/event_orchestrations"),
                ("orchestrations", "orchestrations"),
            ),
            (
                ("get", "/event_orchestrations"),
                ("orchestrations", "orchestrations"),
            ),
            # Disabled
            (("post", "/analytics/raw/incidents"), (None, None)),
        ]
        for (method, path), rval in io_expected:
            self.assertEqual(rval, pagerduty.entity_wrappers(method, path))

    def test_infer_entity_wrapper(self):
        io_expected = [
            (("get", "/users"), "users"),
            (("PoSt", "/users"), "user"),
            (("PUT", "/service/{id}"), "service"),
            (("PUT", "/incidents/{id}/alerts"), "alerts"),
        ]
        for method_path, expected_wrapper in io_expected:
            self.assertEqual(
                expected_wrapper,
                pagerduty.infer_entity_wrapper(*method_path),
            )

    def test_unwrap(self):
        # Response has unexpected type, raise:
        r = Response(200, json.dumps([]))
        self.assertRaises(
            pagerduty.ServerHttpError, pagerduty.unwrap, r, "foo"
        )
        # Response has unexpected structure, raise:
        r = Response(200, json.dumps({"foo_1": {"bar": 1}, "foo_2": "bar2"}))
        self.assertRaises(
            pagerduty.ServerHttpError, pagerduty.unwrap, r, "foo"
        )
        # Response has the expected structure, return the wrapped entity:
        foo_entity = {"type": "foo_reference", "id": "PFOOBAR"}
        r = Response(200, json.dumps({"foo": foo_entity}))
        self.assertEqual(foo_entity, pagerduty.unwrap(r, "foo"))
        # Disabled entity wrapping (wrapper=None), return body as-is
        self.assertEqual({"foo": foo_entity}, pagerduty.unwrap(r, None))


class FunctionDecoratorsTest(unittest.TestCase):
    @patch.object(pagerduty.RestApiV2Client, "put")
    def test_resource_path(self, put_method):
        client = pagerduty.RestApiV2Client("some-key")
        resource_url = "https://api.pagerduty.com/users/PSOMEUSR"
        user = {
            "id": "PSOMEUSR",
            "type": "user",
            "self": resource_url,
            "name": "User McUserson",
            "email": "user@organization.com",
        }
        put_method.return_value = Response(
            200, json.dumps({"user": user}), method="PUT", url=resource_url
        )
        client.rput(user, json=user)
        put_method.assert_called_with(resource_url, json={"user": user})

    def test_wrapped_entities(self):
        do_http_things = MagicMock()
        response = MagicMock()
        do_http_things.return_value = response
        # TODO: make a dummy client class and use that instead
        client = pagerduty.RestApiV2Client("some_key")
        dummy_client = MagicMock()

        def reset_mocks():
            do_http_things.reset_mock()
            response.reset_mock()
            do_http_things.return_value = response
            dummy_client.reset_mock()

        # OK response, good JSON: JSON-decode and unpack response
        response.is_success = True
        response.json.return_value = {"service": {"name": "value"}}
        do_http_things.__name__ = "rput"  # just for instance
        self.assertEqual(
            pagerduty.wrapped_entities(do_http_things)(
                client, "/services/PTHINGY"
            ),
            {"name": "value"},
        )
        reset_mocks()

        # OK response, bad JSON: raise exception.
        response.is_success = True
        do_http_things.__name__ = "rput"  # just for instance
        response.json.side_effect = [ValueError("Bad JSON!")]
        self.assertRaises(
            pagerduty.Error,
            pagerduty.wrapped_entities(do_http_things),
            client,
            "/services",
        )
        reset_mocks()

        # OK response, but the response isn't what we expected: exception.
        do_http_things.reset_mock()
        response.reset_mock()
        response.json = MagicMock()
        response.is_success = True
        do_http_things.return_value = response
        do_http_things.__name__ = "rput"  # just for instance
        response.json.return_value = {"nope": "nopenope"}
        self.assertRaises(
            pagerduty.HttpError,
            pagerduty.wrapped_entities(do_http_things),
            client,
            "/services",
        )
        reset_mocks()

        # Not OK response, raise
        response.reset_mock()
        response.is_success = False
        do_http_things.__name__ = "rput"  # just for instance
        self.assertRaises(
            pagerduty.Error,
            pagerduty.wrapped_entities(do_http_things),
            client,
            "/services",
        )
        reset_mocks()

        # GET /<index>: use a different envelope name
        response.is_success = True
        users_array = [
            {
                "type": "user",
                "email": "user@example.com",
                "summary": "User McUserson",
            }
        ]
        response.json.return_value = {"users": users_array}
        do_http_things.__name__ = "rget"
        dummy_client.url = "https://api.pagerduty.com"
        dummy_client.canonical_path.return_value = "/users"
        dummy_client.entity_wrappers.return_value = ("users", "users")
        self.assertEqual(
            users_array,
            pagerduty.wrapped_entities(do_http_things)(
                dummy_client, "/users", query="user"
            ),
        )
        reset_mocks()

        # Test request body JSON envelope stuff in post/put
        # Response body validation
        do_http_things.__name__ = "rpost"
        user_payload = {"email": "user@example.com", "name": "User McUserson"}
        dummy_client.url = "https://api.pagerduty.com"
        dummy_client.canonical_path.return_value = "/users"
        dummy_client.entity_wrappers.return_value = ("user", "user")
        self.assertRaises(
            pagerduty.Error,
            pagerduty.wrapped_entities(do_http_things),
            dummy_client,
            "/users",
            json=user_payload,
        )
        reset_mocks()
        # Add type property; should work now and automatically pack the user
        # object into a JSON object inside the envelope.
        user_payload["type"] = "user"
        dummy_client.url = "https://api.pagerduty.com"
        dummy_client.canonical_path.return_value = "/users"
        do_http_things.__name__ = "rpost"
        response.is_success = True
        created_user = user_payload.copy()
        created_user["id"] = "P456XYZ"
        response.json.return_value = {"user": created_user}
        self.assertEqual(
            created_user,
            pagerduty.wrapped_entities(do_http_things)(
                dummy_client, "/users", json=user_payload
            ),
        )
        do_http_things.assert_called_with(
            dummy_client, "/users", json={"user": user_payload}
        )

        reset_mocks()
        # Test auto-envelope functionality for multi-update
        incidents = [{"id": "PABC123"}, {"id": "PDEF456"}]
        dummy_client.url = "https://api.pagerduty.com"
        dummy_client.canonical_path.return_value = "/incidents"
        dummy_client.entity_wrappers.return_value = ("incidents", "incidents")
        do_http_things.__name__ = "rput"
        response.is_success = True
        updated_incidents = copy.deepcopy(incidents)
        response.json.return_value = {"incidents": updated_incidents}
        self.assertEqual(
            updated_incidents,
            pagerduty.wrapped_entities(do_http_things)(
                dummy_client, "/incidents", json=incidents
            ),
        )
        # The final value of the json parameter passed to the method (which goes
        # straight to put) should be the plural resource name
        self.assertEqual(
            do_http_things.mock_calls[0][2]["json"], {"incidents": incidents}
        )


class RestApiV2BaseClientTest(ClientTest):

    def test_auth_method(self):
        # TODO: test validation of the pick-one-by-keyword selection interface
        pass

    def test_dict_all(self):
        # TODO: compose a dict (pretty basic)
        pass

    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_get_total_valid(self, get):
        """
        Test RestApiV2Client.get_total for a valid response
        """
        count = 500
        pd_start = "2010-01-01T00:00:00Z"
        now = pagerduty.common.strftime(datetime.datetime.now(timezone.utc))
        get.return_value = Response(
            200,
            json.dumps(
                {
                    "total": count,
                    # Don't care about content, just the total property
                    "log_entries": {},
                }
            ),
        )
        client = pagerduty.RestApiV2Client("token")
        total = client.get_total(
            "/log_entries", params={"since": pd_start, "until": now}
        )
        self.assertEqual(total, count)
        get.assert_called_once_with(
            "/log_entries",
            params={
                "since": pd_start,
                "until": now,
                "total": True,
                "limit": 1,
                "offset": 0,
            },
        )


    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_get_total_invalid(self, get):
        """
        Test RestApiV2Client.get_total for a response that lacks "total"
        """
        get.return_value = Response(200, json.dumps({"log_entries": {}}))
        pd_start = "2010-01-01T00:00:00Z"
        now = pagerduty.common.strftime(datetime.datetime.now(timezone.utc))
        get.return_value = Response(200, json.dumps({"widgets": {}}))
        client = pagerduty.RestApiV2Client("token")
        self.assertRaises(
            pagerduty.ServerHttpError,
            client.get_total,
            "/log_entries",
            params={"since": pd_start, "until": now},
        )


    @patch.object(httpx.Client, "request")
    def test_oauth_headers(self, request):
        """
        A deeper functional test of auth methods
        """
        access_token = "randomly generated lol"
        for auth_type in ("bearer", "oauth2"):
            request.reset_mock()
            client = pagerduty.RestApiV2Client(
                access_token, auth_type=auth_type
            )
            self.assertTrue(
                isinstance(
                    client.auth_method,
                    pagerduty.rest_api_v2_base_client.OAuthTokenAuthMethod
                )
            )
            # Make a request and validate the headers passed to it include the expected
            # header format from the selected AuthMethod:
            request.return_value = Response(200, "{}")
            client.post("/foo", json={})
            request_call = request.mock_calls[0]
            self.assertTrue("headers" in request_call[2])
            self.assertTrue("Authorization" in request_call[2]["headers"])
            self.assertEqual(
                "Bearer " + access_token,
                request_call[2]["headers"]["Authorization"],
            )


    @patch.object(pagerduty.RestApiV2Client, "iter_cursor")
    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_iter_all(self, get, iter_cursor):
        # TODO: Use a dummy class for testing
        client = pagerduty.RestApiV2Client("token")
        client.log = MagicMock()

        # Test: user uses iter_all on an endpoint that supports cursor-based
        # pagination, short-circuit to iter_cursor
        path = "/audit/records"
        cpath = pagerduty.canonical_path("https://api.pagerduty.com", path)
        self.assertTrue(
            cpath in pagerduty.rest_api_v2_client.CURSOR_BASED_PAGINATION_PATHS
        )
        iter_cursor.return_value = []
        passed_kw = {
            "params": {
                "since": "2025-01-01T00:00:00Z",
                "until": "2025-05-19T00:00:00Z",
            },
            "item_hook": lambda x, y, z: print(f"{x}: {y}/{z}"),
            "page_size": 42,
        }
        self.assertEqual(
            [], list(client.iter_all("/audit/records", **passed_kw))
        )
        iter_cursor.assert_called_once_with("/audit/records", **passed_kw)

        # Test: user tries to use iter_all on a singular resource, raise error:
        self.assertRaises(
            pagerduty.UrlError,
            lambda p: list(client.iter_all(p)),
            "users/PABC123",
        )
        # Test: user tries to use iter_all on an endpoint that doesn't actually
        # support pagination, raise error:
        self.assertRaises(
            pagerduty.UrlError,
            lambda p: list(client.iter_all(p)),
            "/analytics/raw/incidents/Q3R8ZN19Z8K083/responses",
        )
        get.side_effect = [
            Response(200, page(0, 30, 10)),
            Response(200, page(1, 30, 10)),
            Response(200, page(2, 30, 10)),
        ]
        # Follow-up to #103: add more odd parameters to the URL
        weirdurl = "https://api.pagerduty.com/users?number=1&filters[]=foo"
        hook = MagicMock()
        items = list(
            client.iter_all(weirdurl, item_hook=hook, total=True, page_size=10)
        )
        self.assertEqual(3, get.call_count)
        self.assertEqual(30, len(items))
        get.assert_has_calls(
            [
                call(
                    weirdurl,
                    params={"limit": 10, "total": "true", "offset": 0},
                ),
                call(
                    weirdurl,
                    params={"limit": 10, "total": "true", "offset": 10},
                ),
                call(
                    weirdurl,
                    params={"limit": 10, "total": "true", "offset": 20},
                ),
            ],
        )
        hook.assert_any_call({"id": 14}, 15, 30)

        # Test stopping iteration on non-success status
        get.reset_mock()
        error_encountered = [
            Response(200, page(0, 50, 10)),
            Response(200, page(1, 50, 10)),
            Response(200, page(2, 50, 10)),
            Response(400, page(3, 50, 10)),  # break
            Response(200, page(4, 50, 10)),
        ]
        get.side_effect = copy.deepcopy(error_encountered)
        self.assertRaises(pagerduty.Error, list, client.iter_all(weirdurl))

        # Test reaching the iteration limit:
        get.reset_mock()
        bigiter = client.iter_all(
            "log_entries", page_size=100, params={"offset": "9901"}
        )
        self.assertRaises(StopIteration, next, bigiter)

        # Test (temporary, until underlying issue in the API is resolved) using
        # the result count to increment offset instead of `limit` reported in
        # API response
        get.reset_mock()
        get.side_effect = [
            Response(200, page(0, 30, None)),
            Response(200, page(1, 30, 42)),
            Response(200, page(2, 30, 2020)),
        ]
        weirdurl = "https://api.pagerduty.com/users?number=1"
        hook = MagicMock()
        items = list(
            client.iter_all(weirdurl, item_hook=hook, total=True, page_size=10)
        )
        self.assertEqual(30, len(items))


    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_iter_cursor(self, get):
        client = pagerduty.RestApiV2Client("token")
        client.log = MagicMock()
        # Test: user tries to use iter_cursor where it won't work, raise:
        self.assertRaises(
            pagerduty.UrlError,
            lambda p: list(client.iter_cursor(p)),
            "incidents",  # Maybe some glorious day, but not as of this writing
        )

        # Test: cursor parameter exchange, stop iteration when records run out,
        # etc. This isn't what the schema of the audit records API actually
        # looks like apart from the entity wrapper, but that doesn't matter for
        # the purpose of this test.
        get.side_effect = [
            Response(200, page_cursor("records", [1, 2, 3], 2)),
            Response(200, page_cursor("records", [4, 5, 6], 5)),
            Response(200, page_cursor("records", [7, 8, 9], None)),
        ]
        self.assertEqual(
            list(client.iter_cursor("/audit/records")), list(range(1, 10))
        )
        # It should send the next_cursor body parameter from the second to
        # last response as the cursor query parameter in the final request
        self.assertEqual(get.mock_calls[-1][2]["params"]["cursor"], 5)

    def test_postprocess(self):
        logger = MagicMock()

        # Test call count and API time
        response = Response(
            201,
            json.dumps({"key": "value"}),
            method="POST",
            url="https://api.pagerduty.com/users/PCWKOPZ/contact_methods",
        )
        client = pagerduty.RestApiV2Client("apikey")
        client.postprocess(response)

        self.assertEqual(
            1, client.api_call_counts["POST /users/{id}/contact_methods"]
        )
        self.assertEqual(
            1.5, client.api_time["POST /users/{id}/contact_methods"]
        )
        response = Response(
            200,
            json.dumps({"key": "value"}),
            method="GET",
            url="https://api.pagerduty.com/users/PCWKOPZ",
        )
        client.postprocess(response)
        self.assertEqual(1, client.api_call_counts["GET /users/{id}"])
        self.assertEqual(1.5, client.api_time["GET /users/{id}"])

        # Test logging
        response = Response(
            500,
            json.dumps({"key": "value"}),
            method="GET",
            url="https://api.pagerduty.com/users/PCWKOPZ/contact_methods",
        )
        client = pagerduty.RestApiV2Client("apikey")
        client.log = logger
        client.postprocess(response)
        if not (sys.version_info.major == 3 and sys.version_info.minor == 5):
            # These assertion methods are not available in Python 3.5
            logger.error.assert_called_once()
            logger.debug.assert_called_once()
        # Make sure we have correct logging params / number of params:
        logger.error.call_args[0][0] % logger.error.call_args[0][1:]
        logger.debug.call_args[0][0] % logger.debug.call_args[0][1:]


    def test_updating_auth_params_propagates_to_auth_method(self):
        """Validate that the secret """
        client = pagerduty.RestApiV2Client("hello-there")
        self.assertEqual("token", client.auth_type)
        self.assertEqual("hello-there", client.auth_method.secret)
        self.assertEqual(
            client.auth_method.auth_header["Authorization"],
            "Token token=hello-there",
        )

        client = pagerduty.RestApiV2Client("hello-there", auth_type="bearer")
        self.assertEqual("bearer", client.auth_type)
        self.assertEqual("hello-there", client.auth_method.secret)
        self.assertEqual(
            client.auth_method.auth_header["Authorization"],
            "Bearer hello-there",
        )

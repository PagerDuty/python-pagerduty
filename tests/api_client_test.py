import json
import logging
import httpx
import random
import sys
from unittest.mock import Mock, MagicMock, patch

import pagerduty
from pagerduty.auth_method import AuthMethod
from pagerduty.errors import UrlError
from common_test import ClientTest
from mocks import Client, Response


class DummyAuthMethod(AuthMethod):
    @property
    def auth_header(self) -> dict:
        return {"Authorization": f"some format idk secret={self.secret}"}

    @property
    def auth_param(self) -> dict:
        return {"secret": self.secret}


class DummyApiClient(pagerduty.ApiClient):
    """
    A minimum-possible full implementation of pagerduty.ApiClient for unit
    testing.
    """

    auth_method_set = False

    def after_set_auth_method(self):
        self.auth_method_set = True

    @property
    def default_base_url(self) -> str:
        return "https://dummy-api.pagerduty.com"

    def normalize_params(self, params: dict) -> dict:
        """
        Add a parameter to indicate that the method was called
        """
        normalized_params = {"new_added_param": "arbitrary-value"}
        normalized_params.update(params)
        return normalized_params

    @property
    def permitted_methods(self) -> tuple:
        return ("DELETE", "GET", "POST", "PUT")

    sleep_timer_base = 0.5


class ApiClientTest(ClientTest):
    def new_client(self):
        return DummyApiClient(DummyAuthMethod("token"))

    def test_auth_method(self):
        client = self.new_client()
        with self.assertRaises(ValueError):
            client.auth_method = None
        client.auth_method_set = False
        client.auth_method = DummyAuthMethod("new_token")
        self.assertTrue(client.auth_method_set)

    def test_cooldown_factor(self):
        rmock = MagicMock()
        with patch.object(random, "random", new=rmock):
            rmock.return_value = 42
            client = self.new_client()
            client.sleep_timer_base = 67
            client.stagger_cooldown = 89
            self.assertTrue(257146, client.cooldown_factor)

    def test_normalize_params(self):
        client = self.new_client()
        self.assertEqual(
            {"new_added_param": "arbitrary-value"}, client.normalize_params({})
        )

    def test_normalize_url(self):
        client = self.new_client()
        self.assertEqual(
            f"{client.url}/some/path", client.normalize_url("/some/path")
        )

    def test_prepare_headers(self):
        client = self.new_client()
        self.assertTrue(
            set(
                client.prepare_headers(
                    "GET", {"X-Arbitrary-Header": "arbitrary-value"}
                ).keys()
            ).issubset(
                set(
                    # HTTPX lowercases headers:
                    [
                        "x-arbitrary-header",
                        "user-agent",
                        "authorization",  # From the AuthMethod
                    ]
                )
            )
        )

    def test_print_debug(self):
        client = self.new_client()
        log = Mock()
        log.setLevel = Mock()
        log.addHandler = Mock()
        client.log = log
        # Enable:
        client.print_debug = True
        log.setLevel.assert_called_once_with(logging.DEBUG)
        self.assertEqual(1, len(log.addHandler.call_args_list))
        self.assertTrue(
            isinstance(
                log.addHandler.call_args_list[0][0][0], logging.StreamHandler
            )
        )
        # Disable:
        log.setLevel.reset_mock()
        log.removeHandler = Mock()
        client.print_debug = False
        log.setLevel.assert_called_once_with(logging.NOTSET)
        self.assertEqual(1, len(log.removeHandler.call_args_list))
        self.assertTrue(
            isinstance(
                log.removeHandler.call_args_list[0][0][0],
                logging.StreamHandler,
            )
        )
        # Setter called via constructor:
        client = DummyApiClient(DummyAuthMethod("not-a-token"), debug=True)
        self.assertTrue(
            isinstance(client._debugHandler, logging.StreamHandler)
        )
        # Setter should be idempotent:
        client.print_debug = False
        client.print_debug = False
        self.assertFalse(hasattr(client, "_debugHandler"))
        client.print_debug = True
        client.print_debug = True
        self.assertTrue(hasattr(client, "_debugHandler"))

    @patch.object(pagerduty.ApiClient, "postprocess")
    def test_request(self, postprocess):
        client = self.new_client()
        # Expected headers:
        headers_get = {
            "Authorization": "some format idk secret=token",  # DummyAuthMethod
            "User-Agent": "python-pagerduty/%s python-httpx/%s Python/%d.%d"
            % (
                pagerduty.__version__,
                httpx.__version__,
                sys.version_info.major,
                sys.version_info.minor,
            ),
        }
        # Check default headers:
        self.assertDictContainsCaseInsensitiveSubset(
            client.prepare_headers("GET"), headers_get
        )
        headers_get.update(client.prepare_headers("GET"))
        # When submitting post/put, the content type should also be set
        headers_post = headers_get.copy()
        headers_post.update({"Content-Type": "application/json"})

        client = self.new_client()
        parent = Client()
        request = MagicMock()
        with patch.object(client, "parent", new=parent):
            parent.request = request
            # Test bad request method
            self.assertRaises(
                pagerduty.Error, client.request, *["poke", "/something"]
            )
            request.assert_not_called()
            # Dummy user
            user = {
                "name": "User McUserson",
                "type": "user",
                "role": "limited_user",
                "email": "user@example.com",
            }
            users = {
                "users": user,
            }

            # Test basic GET & profiling
            return_value = Response(200, json.dumps(users))
            request.return_value = return_value
            r = client.request("get", "/users")
            postprocess.assert_called_with(return_value)
            request.assert_called_once_with(
                "GET",
                f"{client.url}/users",
                headers=client.prepare_headers("GET"),
                timeout=pagerduty.TIMEOUT,
                auth=None,
                follow_redirects=False,
                cookies=None,
            )
            request.reset_mock()

            # Test POST/PUT (in terms of code coverage they're identical)
            request.return_value = Response(201, json.dumps({"user": user}))
            client.request("post", "users", json={"user": user})
            request.assert_called_once_with(
                "POST",
                f"{client.url}/users",
                headers=client.prepare_headers("POST"),
                json={
                    "user": user,
                    "secret": "token",  # From DummyAuthMethod
                },
                timeout=pagerduty.TIMEOUT,
                auth=None,
                follow_redirects=False,
                cookies=None,
            )
            request.reset_mock()

            # Test GET with parameters and using a HTTP verb method
            request.return_value = Response(200, json.dumps({"users": [user]}))
            user_query = {"query": "user@example.com"}
            r = client.get("/users", params=user_query)
            expected_params = {
                "new_added_param": "arbitrary-value"  # From normalize_params
            }
            expected_params.update(user_query)
            request.assert_called_once_with(
                "GET",
                f"{client.url}/users",
                headers=client.prepare_headers("GET"),
                params=expected_params,
                follow_redirects=False,
                timeout=pagerduty.TIMEOUT,
                auth=None,
                cookies=None,
                extensions=None,
            )
            request.reset_mock()

            # Test a POST request with additional headers
            request.return_value = Response(
                201, json.dumps({"user": user}), method="POST"
            )
            headers_special = {"X-Tra-Special-Header": "1"}
            r = client.post(
                "/users/PD6LYSO/future_endpoint",
                headers=headers_special,
                json={"user": user},
            )
            request.assert_called_once_with(
                "POST",
                f"{client.url}/users/PD6LYSO/future_endpoint",
                content=None,
                data=None,
                files=None,
                json={
                    "user": user,
                    "secret": "token",  # From DummyAuthMethod
                },
                params=None,
                headers=client.prepare_headers(
                    "POST", user_headers=headers_special
                ),
                timeout=pagerduty.TIMEOUT,
                follow_redirects=False,
                extensions=None,
                auth=None,
                cookies=None,
            )
            request.reset_mock()

            # Test hitting the rate limit
            request.side_effect = [
                Response(429, json.dumps({"error": {"message": "chill out"}})),
                Response(429, json.dumps({"error": {"message": "chill out"}})),
                Response(200, json.dumps({"user": user})),
            ]
            with patch.object(pagerduty.api_client.time, "sleep") as sleep:
                r = client.get("/users")
                self.assertTrue(
                    r.is_success
                )  # should only return after success
                self.assertEqual(3, request.call_count)
                self.assertEqual(2, sleep.call_count)
            request.reset_mock()
            request.side_effect = None

            # Test a 401 (should raise Exception)
            request.return_value = Response(
                401,
                json.dumps(
                    {
                        "error": {
                            "code": 2006,
                            "message": "You shall not pass.",
                        }
                    }
                ),
            )
            self.assertRaises(
                pagerduty.HttpError, client.request, "get", "/services"
            )
            request.reset_mock()

            # Test retry logic:
            with patch.object(pagerduty.api_client.time, "sleep") as sleep:
                # Test getting a connection error and succeeding the final time.
                returns = [
                    pagerduty.api_client.TransportError("D'oh!")
                ] * client.max_network_attempts
                returns.append(Response(200, json.dumps({"user": user})))
                request.side_effect = returns
                with patch.object(client, "cooldown_factor") as cdf:
                    cdf.return_value = 2.0
                    r = client.get("/users/P123456")
                    self.assertEqual(
                        client.max_network_attempts + 1, request.call_count
                    )
                    self.assertEqual(
                        client.max_network_attempts, sleep.call_count
                    )
                    self.assertEqual(
                        client.max_network_attempts, cdf.call_count
                    )
                    self.assertTrue(r.is_success)
                request.reset_mock()
                sleep.reset_mock()

                # Now test handling a non-transient error when the client
                # library itself hits odd issues that it can't handle, i.e.
                # network, and that the raised exception includes context:
                raises = [pagerduty.api_client.TransportError("D'oh!")] * (
                    client.max_network_attempts + 1
                )
                request.side_effect = raises
                try:
                    client.get("/users")
                    self.assertTrue(
                        False,
                        msg="Exception not raised after retry maximum count reached",
                    )
                except pagerduty.Error as e:
                    self.assertEqual(e.__cause__, raises[-1])
                except Exception as e:
                    self.assertTrue(
                        False,
                        msg="Raised exception not of the "
                        f"expected class; was {e.__class__}",
                    )
                self.assertEqual(
                    client.max_network_attempts + 1, request.call_count
                )
                self.assertEqual(client.max_network_attempts, sleep.call_count)

                # Test custom retry logic:
                client.retry[404] = 3
                request.side_effect = [
                    Response(404, json.dumps({})),
                    Response(404, json.dumps({})),
                    Response(200, json.dumps({"user": user})),
                ]
                with patch.object(client, "cooldown_factor") as cdf:
                    cdf.return_value = 2.0
                    r = client.get("/users/P123456")
                    self.assertEqual(200, r.status_code)
                    self.assertEqual(2, cdf.call_count)
                # Test retry logic with too many 404s
                client.retry[404] = 1
                request.side_effect = [
                    Response(404, json.dumps({})),
                    Response(404, json.dumps({})),
                    Response(200, json.dumps({"user": user})),
                ]
                client.log = MagicMock()
                r = client.get("/users/P123456")
                self.assertEqual(404, r.status_code)

    def test_stagger_cooldown(self):
        client = self.new_client()
        with self.assertRaises(ValueError):
            client.stagger_cooldown = None

    def test_trunc_key(self):
        client = self.new_client()
        self.assertEqual("*oken", client.trunc_key)

    def test_url(self):
        client = self.new_client()
        with self.assertRaises(UrlError):
            client.url = "http://lol-so-secure.url"

    def test_user_agent(self):
        client = self.new_client()
        # Because unit tests sometimes run into the package introspection
        # stopgap, we need to use \S+ to match the version.
        self.assertRegex(
            client.user_agent,
            r"""python-pagerduty/\S+ python-httpx/[0-9.]+ """
            r"""Python/[0-9]+\.[0-9]+""",
        )

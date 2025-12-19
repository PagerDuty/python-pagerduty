import copy
import json
import logging
import httpx
import sys
from unittest.mock import Mock, MagicMock, patch

import pagerduty
from pagerduty.auth_method import AuthMethod
from common_test import ClientTest, Client, Response


class DummyAuthMethod(AuthMethod):
    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"some format idk secret={self.secret}"}

    @property
    def auth_param(self) -> dict:
        return {"secret": self.secret}


class DummyApiClient(pagerduty.ApiClient):
    """
    A minimum-possible full implementation of pagerduty.ApiClient for unit
    testing.
    """

    def after_set_auth_method(self):
        # TODO: a signal to indicate this method is being called correctly
        pass

    def normalize_params(self, params: dict) -> dict:
        # TODO: a signal to indicate this method is being called correctly
        pass

    permitted_methods = ()
    # TODO: the range of requests used in mocks

    def postprocess(self, response: Response):
        # TODO: a signal to indicate this method is being called correctly
        pass

    sleep_timer_base = 0.5


class ApiClientTest(ClientTest):
    def test_auth_method(self):
        # TODO: ValueError raise
        pass

    # def cooldown_factor(self) -> float:
    # TODO: mock random(), self.stagger_cooldown and sleep_timer_base

    def test_normalize_params(self):
        # TODO: check for the signal in the class.
        pass

    def test_normalize_url(self):
        # TODO: calls normalize_url correctly
        pass

    # def prepare_headers(
    #    self, method: str, user_headers: Optional[dict] = None
    # ) -> dict:
    # TODO: Define user agent
    # TODO: Set JSON content type when sending a payload-bearing request
    # TODO: apply user headers with the expected precedence of user headers
    # TODO: add auth_method's auth header, if any.

    def test_print_debug(self):
        client = DummyApiClient(DummyAuthMethod("token"))
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

    @patch.object(pagerduty.RestApiV2Client, "postprocess")
    def test_request(self, postprocess):
        # TODO: Refactor this to use the dummy client class
        client = pagerduty.RestApiV2Client("12345")
        parent = Client()
        request = MagicMock()
        # Expected headers:
        headers_get = {
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Authorization": "Token token=12345",
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
        parent.headers = headers_get

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
            users = {"users": user}

            # Test basic GET & profiling
            request.return_value = Response(200, json.dumps(users))
            r = client.request("get", "/users")
            postprocess.assert_called_with(request.return_value)
            request.assert_called_once_with(
                "GET",
                "https://api.pagerduty.com/users",
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
                "https://api.pagerduty.com/users",
                headers=client.prepare_headers("POST"),
                json={"user": user},
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
            request.assert_called_once_with(
                "GET",
                "https://api.pagerduty.com/users",
                headers=client.prepare_headers("GET"),
                params=user_query,
                follow_redirects=False,
                timeout=pagerduty.TIMEOUT,
                auth=None,
                cookies=None,
                extensions=None,
            )
            request.reset_mock()

            # Test GET with one array-type parameter not suffixed with []
            request.return_value = Response(200, json.dumps({"users": [user]}))
            user_query = {"query": "user@example.com", "team_ids": ["PCWKOPZ"]}
            modified_user_query = copy.deepcopy(user_query)
            modified_user_query["team_ids[]"] = user_query["team_ids"]
            del modified_user_query["team_ids"]
            r = client.get("/users", params=user_query)
            request.assert_called_once_with(
                "GET",
                "https://api.pagerduty.com/users",
                params=modified_user_query,
                headers=client.prepare_headers("GET"),
                cookies=None,
                follow_redirects=False,
                timeout=pagerduty.TIMEOUT,
                extensions=None,
                auth=None,
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
                "https://api.pagerduty.com/users/PD6LYSO/future_endpoint",
                content=None,
                data=None,
                files=None,
                json={"user": user},
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

    # def stagger_cooldown(self, val: Union[float, int]):
    # TODO: ValueError

    # def trunc_key(self) -> str:
    # TODO: mock auth_method and test that trunc_secret is set.

    # def url(self) -> str:
    # TODO: UrlError

    def test_trunc_key(self):
        client = pagerduty.RestApiV2Client("abcd1234")
        self.assertEqual("*1234", client.trunc_key)

    # def user_agent(self) -> str:
    # #TODO: Matches a "looks like this" regex

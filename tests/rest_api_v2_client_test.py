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

from common_test import ClientTest
from mocks import Client, Response


import pagerduty
from pagerduty.rest_api_v2_base_client import OAuthTokenAuthMethod


def page_alert_grouping_settings(after: Optional[str], limit: int) -> str:
    """
    Generate a dummy page for testing alert grouping settings API's special pagination
    """
    page = {
        # Method is agnostic to the internal schema of settings entries:
        "alert_grouping_settings": [{"foo": f"bar{i}"} for i in range(limit)],
    }
    if after is not None:
        page["after"] = after
    return json.dumps(page)


def page_analytics_raw_incident_data(limit: int, last: str, more: bool) -> str:
    """
    Generate a dummy page for testing the special pagination in the analytics API

    The test is agnostic to content and most of the response properties. It only needs
    to mock up the properties that are actually used.
    """
    body = {"data": [{"foo": f"bar_{i}"} for i in range(limit)], "more": more}
    if last:
        body["last"] = last
    return json.dumps(body)


class RestApiV2ClientTest(ClientTest):
    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_api_key_access(self, get):
        token = "i am a potato"
        # Account-type token
        client = pagerduty.RestApiV2Client(token)
        get.side_effect = [
            Response(
                400,
                # The expected format of the error response for account-type
                # tokens, valid/current as of 2025-11-14
                '{"error": "Because this request was made using an '
                "account-level access token, we were unable to determine the "
                "user's identity. Please use a user-level token.\"}",
            )
        ]
        self.assertEqual("account", client.api_key_access)
        get.reset_mock()

        # Invalid response: set to None and log error
        client = pagerduty.RestApiV2Client(token)
        get.side_effect = [
            Response(400, '{"error": "YOU LOSE, GOOD DAY SIR"}')
        ]
        self.assertEqual(None, client.api_key_access)
        get.reset_mock()

        # User token: success response / a user JSON
        client = pagerduty.RestApiV2Client(token)
        get.side_effect = [
            Response(
                200,
                json.dumps(
                    {
                        "user": {
                            "name": "User McUserson",
                            "email": "demitri@pagerduty.com",
                            "id": "POOPBUG",
                        }
                    }
                ),
            )
        ]
        self.assertEqual("user", client.api_key_access)

    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_account_has_ability(self, get):
        access_token = "tokenmctokenface"
        client = pagerduty.RestApiV2Client(access_token)
        cases = {
            204: True,
            402: False,
            403: pagerduty.HttpError,
            404: pagerduty.HttpError,
        }
        for status_code, expected in cases.items():
            get.side_effect = [Response(status_code, "")]
            if type(expected) is bool:
                self.assertEqual(
                    expected, client.account_has_ability("whatever")
                )
            elif issubclass(expected, Exception):
                with self.assertRaises(expected):
                    client.account_has_ability("whatever")
            get.reset_mock()


    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    def test_find(self, iter_all):
        client = pagerduty.RestApiV2Client("token")
        iter_all.return_value = iter(
            [
                {
                    "type": "user",
                    "name": "Someone Else",
                    "email": "some1@me.me.me",
                    "f": 1,
                },
                {
                    "type": "user",
                    "name": "Space Person",
                    "email": "some1@me.me ",
                    "f": 2,
                },
                {
                    "type": "user",
                    "name": "Someone Personson",
                    "email": "some1@me.me",
                    "f": 3,
                },
                {
                    "type": "user",
                    "name": "Numeric Fields",
                    "email": "test@example.com",
                    "f": 5,
                },
            ]
        )
        self.assertEqual(
            "Someone Personson",
            client.find("users", "some1@me.me", attribute="email")["name"],
        )
        iter_all.assert_called_with("users", params={"query": "some1@me.me"})
        self.assertEqual(
            "Numeric Fields", client.find("users", 5, attribute="f")["name"]
        )

    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_iter_alert_grouping_settings(self, get):
        """
        Test the special pagination style of the alert grouping settings API.
        """
        AFTER_1 = "abcd1234"
        AFTER_2 = "defg5678"
        client = pagerduty.RestApiV2Client("token")
        get.side_effect = [
            Response(200, page_alert_grouping_settings(AFTER_1, 2)),
            Response(200, page_alert_grouping_settings(AFTER_2, 2)),
            Response(200, page_alert_grouping_settings(None, 2)),
        ]
        data = list(client.iter_alert_grouping_settings())
        self.assertEqual(6, len(data))
        self.assertEqual(3, get.call_count)
        # A page's "after" cursor is the value of "after" from the page before it:
        self.assertEqual(AFTER_1, get.call_args_list[1][1]["params"]["after"])


    @patch.object(pagerduty.RestApiV2Client, "post")
    def test_iter_analytics_raw_incidents(self, post):
        LIMIT = 10
        client = pagerduty.RestApiV2Client("token")
        # Test: exit if "more" indicates the end of the data set, use custom limit
        LAST_1 = "abcd1234"
        LAST_2 = "defg5678"
        post.side_effect = [
            Response(
                200, page_analytics_raw_incident_data(LIMIT, LAST_1, True)
            ),
            Response(
                200, page_analytics_raw_incident_data(LIMIT, LAST_2, False)
            ),
        ]
        data = list(
            client.iter_analytics_raw_incidents({"bar": "baz"}, limit=LIMIT)
        )
        self.assertEqual(LIMIT * 2, len(data))
        self.assertEqual(2, post.call_count)
        self.assertEqual(
            LAST_1, post.call_args_list[1][1]["json"]["starting_after"]
        )
        # Test: exit if the "last" property is not set, use default limit
        post.reset_mock()
        post.side_effect = [
            Response(200, page_analytics_raw_incident_data(LIMIT, None, True)),
            Response(200, page_analytics_raw_incident_data(LIMIT, None, True)),
        ]
        data = list(client.iter_analytics_raw_incidents({"bar": "baz"}))
        self.assertEqual(1, post.call_count)
        self.assertEqual(
            client.default_page_size,
            post.call_args_list[0][1]["json"]["limit"],
        )


    # iter_history tests
    #
    # Each call to iter_history will result in a "total" request (limit=1, offset=0)
    # followed by iter_all sub-requests (if done recursing) for each interval, or a
    # series of recursive calls to iter_history. The test data here don't reflect
    # anything realistic, especially because the total number of records changes
    # depending on the level of recursion, but the stubbing/mocking return values are
    # just to test that the logic works.

    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    @patch.object(pagerduty.RestApiV2Client, "get_total")
    def test_iter_history_recursion_1s(self, get_total, iter_all):
        """
        Test iter_history stop-iteration on hitting the minimum interval length
        """
        client = pagerduty.RestApiV2Client("token")
        # Checks for "total" in each sub-interval: the first for the whole 2s, the
        # second for the first 1-second sub-interval and the third for the second.
        get_total.side_effect = [
            # Top level: total is over the limit; bisect
            pagerduty.ITERATION_LIMIT + 2,
            # Level 1, sub-interval 1: call iter_all; max total not exceeded
            1,
            # Level 1, sub-interval 2: call iter_all; max total exceeded but interval=1s
            pagerduty.ITERATION_LIMIT + 1,
        ]
        iter_all.side_effect = [
            iter([{"type": "log_entry"}]),
            iter([{"type": "log_entry"}]),
        ]

        now = datetime.datetime.now(timezone.utc)
        future3 = now + datetime.timedelta(seconds=2)
        results = list(client.iter_history("/log_entries", now, future3))
        self.assertEqual(2, len(iter_all.mock_calls))
        self.assertEqual([{"type": "log_entry"}] * 2, results)

    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    @patch.object(pagerduty.RestApiV2Client, "get_total")
    def test_iter_history_recursion_limit(self, get_total, iter_all):
        """
        Test iter_history stop-iteration on hitting the recursion depth limit
        """
        # Adjust the recursion limit so we only need 1 level of stub data:
        client = pagerduty.RestApiV2Client("token")
        original_recursion_limit = pagerduty.rest_api_v2_client.RECURSION_LIMIT
        pagerduty.rest_api_v2_client.RECURSION_LIMIT = 1
        # Checks for "total" in each sub-interval: The expected breakdown of 3s is a 1s
        # interval followed by a 2s interval at the first level of recursion, and then
        # two 1s intervals.
        get_total.side_effect = [
            # Top level: total is over the limit; bisect
            pagerduty.ITERATION_LIMIT + 2,
            # Level 1, sub-interval 1: call iter_all; max total not exceeded
            1,
            # Level 1, sub-interval 2: call iter_all; max recursion depth reached
            pagerduty.ITERATION_LIMIT + 1,
        ]
        iter_all.side_effect = [
            iter([{"type": "log_entry"}]),
            iter([{"type": "log_entry"}]),
        ]
        now = datetime.datetime.now(timezone.utc)
        future6 = now + datetime.timedelta(seconds=6)
        results = list(client.iter_history("/log_entries", now, future6))
        self.assertEqual([{"type": "log_entry"}] * 2, results)
        self.assertEqual(2, len(iter_all.mock_calls))
        pagerduty.rest_api_v2_client.RECURSION_LIMIT = original_recursion_limit

    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    @patch.object(pagerduty.RestApiV2Client, "get_total")
    @patch.object(pagerduty.RestApiV2Client, "iter_cursor")
    def test_iter_history_cursor_callout(
        self, iter_cursor, get_total, iter_all
    ):
        """
        Validate the method defers to iter_cursor when used with cursor-based pagination
        """
        client = pagerduty.RestApiV2Client("token")
        now = datetime.datetime.now(timezone.utc)
        future6 = now + datetime.timedelta(seconds=6)
        iter_cursor.side_effect = [iter([{"type": "record"}])]
        list(
            client.iter_history(
                "/audit/records", now, future6, params={"actions": ["delete"]}
            )
        )
        iter_all.assert_not_called()
        get_total.assert_not_called()
        iter_cursor.assert_called_once()
        self.assertEqual("/audit/records", iter_cursor.mock_calls[0][1][0])
        self.assertEqual(
            ["delete"], iter_cursor.mock_calls[0][2]["params"]["actions"]
        )

    def test_iter_history_invalid_url(self):
        client = pagerduty.RestApiV2Client("token")
        now = datetime.datetime.now(timezone.utc)
        future6 = now + datetime.timedelta(seconds=6)
        # Ooops, wrong URL
        with self.assertRaises(pagerduty.UrlError):
            list(
                client.iter_history(
                    "/services",  # Oops
                    now,
                    future6,
                )
            )

    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    def test_iter_incident_notes_single_incident(self, iter_all):
        """
        Validate proper function when requesting incident notes for a given incident ID
        """
        INCIDENT_ID = "Q789GHI"
        iter_all.return_value = iter(
            [
                {"type": "trigger_log_entry", "summary": "server on fire"},
                {"type": "annotate_log_entry", "summary": "used extinguisher"},
                {
                    "type": "annotate_log_entry",
                    "summary": "will not reboot, replacing.",
                },
                {"type": "resolve_log_entry"},
            ]
        )
        client = pagerduty.RestApiV2Client("token")

        notes = list(
            client.iter_incident_notes(
                incident_id=INCIDENT_ID, params={"team_ids[]": ["Q1GN0R3M3"]}
            )
        )
        self.assertEqual(2, len(notes))
        self.assertEqual(
            f"/incidents/{INCIDENT_ID}/log_entries", iter_all.call_args[0][0]
        )
        params = iter_all.call_args_list[0][1]["params"]
        self.assertFalse("team_ids" in params)
        self.assertFalse("team_ids[]" in params)

    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    def test_iter_incident_notes_teams_filter(self, iter_all):
        """
        Validate proper function when requesting incident notes for specified teams
        """
        TEAM_ID_1 = "QABCDE12345"
        TEAM_ID_2 = "QFGHIJ67890"
        iter_all.return_value = iter(
            [
                {"type": "trigger_log_entry", "summary": "server on fire"},
                {"type": "annotate_log_entry", "summary": "used extinguisher"},
                {
                    "type": "annotate_log_entry",
                    "summary": "will not reboot, replacing.",
                },
                {"type": "resolve_log_entry"},
            ]
        )
        client = pagerduty.RestApiV2Client("token")
        notes = list(
            client.iter_incident_notes(
                params={"team_ids[]": [TEAM_ID_1, TEAM_ID_2]}
            )
        )
        self.assertEqual(2, len(notes))
        self.assertEqual("/log_entries", iter_all.call_args[0][0])
        params = iter_all.call_args_list[0][1]["params"]
        self.assertTrue("team_ids[]" in params)
        self.assertEqual([TEAM_ID_1, TEAM_ID_2], params["team_ids[]"])

    @patch.object(pagerduty.RestApiV2Client, "rput")
    @patch.object(pagerduty.RestApiV2Client, "rpost")
    @patch.object(pagerduty.RestApiV2Client, "iter_all")
    def test_persist(self, iterator, creator, updater):
        user = {
            "name": "User McUserson",
            "email": "user@organization.com",
            "type": "user",
        }
        # Do not create if the user exists already (default)
        iterator.return_value = iter([user])
        client = pagerduty.RestApiV2Client("apiKey")
        client.persist("users", "email", user)
        creator.assert_not_called()
        # Call client.rpost to create if the user does not exist
        iterator.return_value = iter([])
        client.persist("users", "email", user)
        creator.assert_called_with("users", json=user)
        # Call client.rput to update an existing user if update is True
        iterator.return_value = iter([user])
        new_user = dict(user)
        new_user.update(
            {
                "job_title": "Testing the app",
                "self": "https://api.pagerduty.com/users/PCWKOPZ",
            }
        )
        client.persist("users", "email", new_user, update=True)
        updater.assert_called_with(new_user, json=new_user)
        # Call client.rput to update but w/no change so no API PUT request:
        updater.reset_mock()
        existing_user = dict(new_user)
        iterator.return_value = iter([existing_user])
        client.persist("users", "email", new_user, update=True)
        updater.assert_not_called()


    @patch.object(pagerduty.RestApiV2Client, "get")
    def test_rget(self, get):
        response200 = Response(
            200,
            '{"user":{"type":"user_reference",'
            '"email":"user@example.com","summary":"User McUserson"}}',
        )
        get.return_value = response200
        s = pagerduty.RestApiV2Client("token")
        self.assertEqual(
            {
                "type": "user_reference",
                "email": "user@example.com",
                "summary": "User McUserson",
            },
            s.rget("/users/P123ABC"),
        )
        # This is (forcefully) valid JSON but no matter; it should raise
        # PDClientErorr nonetheless
        response404 = Response(404, '{"user": {"email": "user@example.com"}}')
        get.reset_mock()
        get.return_value = response404
        self.assertRaises(pagerduty.Error, s.rget, "/users/P123ABC")

    @patch.object(pagerduty.RestApiV2Client, "rget")
    def test_subdomain(self, rget):
        rget.return_value = [{"html_url": "https://something.pagerduty.com"}]
        client = pagerduty.RestApiV2Client("key")
        self.assertEqual("something", client.subdomain)
        self.assertEqual("something", client.subdomain)
        rget.assert_called_once_with("users", params={"limit": 1})

    @patch.object(pagerduty.RestApiV2Client, "rget")
    def test_subdomain_cleared_with_auth_method(self, rget):
        """Test that updating auth_method resets the subdomain getter"""
        rget.return_value = [{"html_url": "https://something.pagerduty.com"}]
        client = pagerduty.RestApiV2Client("key")
        self.assertEqual("something", client.subdomain)

        # updating the auth method should clear the subdomain
        client.auth_method = OAuthTokenAuthMethod("token")
        self.assertEqual(None, client._subdomain)

        # and we should get a new subdomain when next accessed
        rget.return_value = [{"html_url": "https://another-one.pagerduty.com"}]
        self.assertEqual("another-one", client.subdomain)


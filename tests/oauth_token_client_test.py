import json
import unittest
from unittest.mock import patch

import requests

from mocks import Response
from pagerduty import OAuthTokenClient
from pagerduty.common import (
    datetime_to_relative_seconds,
    relative_seconds_to_datetime
)
from pagerduty.rest_api_v2_client import RestApiV2Client

class OAuthTokenClientTest(unittest.TestCase):

    def new_client(self):
        client_secret = 'notaclientsecret'
        client_id     = 'notaclientid'
        client = OAuthTokenClient(client_secret, client_id)
        return (client_secret, client_id, client)

    def test_get_authorize_url(self):
        client_id = 'abc123'
        scope = 'def456'
        redirect_uri = 'https://example.com/nope'
        uri_encoded = 'https%3A%2F%2Fexample.com%2Fnope'
        self.assertEqual(
            "https://identity.pagerduty.com/oauth/authorize?" + \
                f"client_id={client_id}&redirect_uri={uri_encoded}&" +\
                f"response_type=code&scope={scope}",
            OAuthTokenClient.get_authorize_url(client_id, scope, redirect_uri)
        )

    @patch.object(requests.Session, 'request')
    def test_get_new_token(self, request):
        (client_secret, client_id, client) = self.new_client()
        # The following adapted from the documentation page
        request.return_value = Response(200, json.dumps({
          "client_info":"prefix_legacy_app",
          "id_token":"super_long_jwt_string",
          "token_type":"bearer",
          "access_token":"not_really_an_access_token",
          "refresh_token":"not_really_a_refresh_token",
          "scope":"openid write",
          "expires_in":864000
        }))
        response = client.get_new_token(foo='bar', bar='baz')
        # Use a small epsilon instead of exact equality to avoid flakiness:
        self.assertTrue(
            abs(864000 - datetime_to_relative_seconds(response['expiration_date'])) < 1
        )
        request.assert_called_once()
        calls = request.mock_calls
        self.assertEqual(
            'https://identity.pagerduty.com/oauth/token',
            calls[0][1][1]
        )
        self.assertEqual(
            {
                'client_id': client_id,
                'client_secret': client_secret,
                'foo': 'bar',
                'bar': 'baz'
            },
            calls[0][2]['data']
        )
        self.assertEqual(
            "application/x-www-form-urlencoded",
            calls[0][2]['headers']['Content-Type']
        )

    @patch.object(OAuthTokenClient, 'get_new_token')
    def test_get_new_token_from_code(self, get_new_token):
        (client_secret, client_id, client) = self.new_client()
        auth_code = '12345'
        scope = 'nope'
        redirect_uri = 'http://example.com/foo'
        client.get_new_token_from_code(auth_code, scope, redirect_uri)
        get_new_token.assert_called_once_with(
            grant_type = 'authorization_code',
            code = auth_code,
            scope = scope,
            redirect_uri = redirect_uri
        )

    @patch.object(OAuthTokenClient, 'get_new_token')
    def test_get_refreshed_token(self, get_new_token):
        (client_secret, client_id, client) = self.new_client()
        refresh_token = 'notarefreshtoken'
        client.get_refreshed_token(refresh_token)
        get_new_token.assert_called_once_with(
            grant_type = 'refresh_token',
            refresh_token = refresh_token
        )

    @patch.object(OAuthTokenClient, 'get_new_token')
    def test_get_scoped_app_token(self, get_new_token):
        (client_secret, client_id, client) = self.new_client()
        scope = 'nope'
        client.get_scoped_app_token(scope)
        get_new_token.assert_called_once_with(
            grant_type = 'client_credentials',
            scope = scope
        )

    @patch.object(OAuthTokenClient, 'get_refreshed_token')
    def test_refresh_client_skip_refresh(self, get_refreshed_token):
        """
        Test using refresh_client when the token is fresh enough to keep using it
        """
        (client_secret, client_id, client) = self.new_client()
        fresh_enough_s_in_future = client.early_refresh_buffer + 864000
        existing_access_token = 'not_an_access_token'
        rest_client, auth = client.refresh_client(
            existing_access_token,
            'not_a_refresh_token',
            expiration_date=relative_seconds_to_datetime(fresh_enough_s_in_future)
        )

        self.assertIsNone(auth)
        self.assertIsInstance(rest_client, RestApiV2Client)
        self.assertEqual(existing_access_token, rest_client.auth_method.secret)
        get_refreshed_token.assert_not_called()

    @patch.object(OAuthTokenClient, 'get_refreshed_token')
    def test_refresh_client_perform_refresh(self, get_refreshed_token):
        """
        Test using refresh_client when the token is old enough to warrant a refresh
        """
        (client_secret, client_id, client) = self.new_client()
        not_far_enough_in_future = client.early_refresh_buffer - 3600
        freshly_made_expires_in = 864000
        api_key_old = 'not_an_access_token'
        api_key_new = "not_the_new_access_token"
        refresh_token = "not_the_refresh_token"
        api_url = 'https://api.eu.pagerduty.com'
        from_email = "someone@example.com"
        expiration_date = relative_seconds_to_datetime(not_far_enough_in_future)
        expiration_date_new = relative_seconds_to_datetime(freshly_made_expires_in)
        get_refreshed_token.return_value = {
          "client_info": "prefix_legacy_app",
          "id_token": "not_an_id_token",
          "token_type": "bearer",
          "access_token": api_key_new,
          "refresh_token": refresh_token,
          "scope": "openid write",
          "expires_in": 864000,
          "expiration_date": expiration_date_new
        }
        rest_client, auth = client.refresh_client(
            api_key_old,
            refresh_token,
            expiration_date,
            base_url = api_url,
            default_from = from_email,
            debug = True
        )
        get_refreshed_token.assert_called_once_with(refresh_token)
        self.assertIs(dict, type(auth))
        self.assertIsInstance(rest_client, RestApiV2Client)
        self.assertEqual(api_key_new, rest_client.auth_method.secret)
        self.assertEqual(api_url, rest_client.url)
        self.assertEqual(from_email, rest_client.default_from)
        self.assertEqual(True, rest_client.print_debug)

import json
import unittest

from unittest.mock import Mock, MagicMock, patch, call

from mocks import Response
from pagerduty import OAuthTokenClient
from pagerduty.common import datetime_to_relative_seconds

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

    @patch.object(OAuthTokenClient, 'post')
    def test_get_new_token(self, post):
        (client_secret, client_id, client) = self.new_client()
        # The following adapted from the documentation page
        post.return_value = Response(200, json.dumps({
          "client_info":"prefix_legacy_app",
          "id_token":"super_long_jwt_string",
          "token_type":"bearer",
          "access_token":"not_really_an_access_token",
          "refresh_token":"not_really_a_refresh_token",
          "scope":"openid write",
          "expires_in":864000
        }))
        response = client.get_new_token(foo='bar', bar='baz')
        # Using a small epsilon vs. exact equals to avoid flakiness:
        self.assertTrue(
            abs(864000 - datetime_to_relative_seconds(response['expiration_date'])) < 1
        )
        post.assert_called_once_with(
            '/oauth/token',
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'foo': 'bar',
                'bar': 'baz'
            },
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
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

    def test_refresh_client(self):
        pass

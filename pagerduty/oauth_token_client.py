import urllib.parse
from typing import Optional, Tuple

from copy import deepcopy

from requests import Response

from . api_client import ApiClient
from . common import (
    datetime_to_relative_seconds,
    relative_seconds_to_datetime,
    successful_response,
    try_decoding
)
from . errors import ServerHttpError
from . rest_api_v2_client import RestApiV2Client

class OAuthTokenClient(ApiClient):
    """
    Client with helpers for performing an OAuth exchange to obtain an access token.

    Tokens obtained using the client can then be used to authenticate REST API clients,
    e.g.

    .. code-block:: python

        oauth_exchange_client = pagerduty.OAuthTokenClient(client_secret, client_id)
        oauth_response = oauth_exchange_client.get_scoped_app_token('read')
        client = pagerduty.RestApiV2Client(oauth_response['access_token'], auth_type='bearer')

    Requires `registering a PagerDuty App
    <https://developer.pagerduty.com/docs/register-an-app>`_ to obtain the necessary
    credentials, and must be used in the context of an OAuth2 authorization flow.

    For further details, refer to:

    - `OAuth Functionality <https://developer.pagerduty.com/docs/oauth-functionality>`_
    - `User OAuth Token via Code Grant <https://developer.pagerduty.com/docs/user-oauth-token-via-code-grant>`_
    - `Obtaining an App OAuth Token <https://developer.pagerduty.com/docs/app-oauth-token>`_
    """

    permitted_methods = ('POST',)

    url = 'https://identity.pagerduty.com'

    early_refresh_buffer = 86400
    """
    Number of seconds before the expiration date to perform a token refresh.

    Used when constructing a :class:`RestApiV2Client`; if the current date/time is
    after the expiration date, or less than this number of seconds before it, a token
    refresh is first performed.

    If the application is expected to use the resulting client object for more than this
    amount of time between each new call to :attr:`refresh_client`, this value can be
    set higher.

    By default, this is 24 hours.
    """

    def __init__(self, client_secret: str, client_id: str, debug=False):
        """
        Create an OAuth token client

        :param client_secret:
            The secret associated with the application.
        :param client_id:
            The client ID provided when registering the application.
        :param debug:
            Passed to the parent constructor as the ``debug`` argument. See:
            :class:`ApiClient`
        """
        super(OAuthTokenClient, self).__init__(client_secret, debug=debug)
        self.client_id = client_id

    def amended_auth_response(self, response: Response) -> dict:
        """
        Amends the auth response map as necessary for other functionality.

        :param auth_response:
            A response from the /oauth/token endpoint as a dictionary.
        :returns:
            The same response from the API in dictionary form with an additional key
            ``expiration_date`` containing the expiration date/time of the token in
            ISO8601 format. This value can then be used in :attr:`refresh_client`.
        """
        response_json = try_decoding(successful_response(response))
        if 'expires_in' not in response_json:
            raise ServerHttpError(
                "Auth response did not include expected key \"expires_in\".",
                response
            )
        response_json.update({
            'expiration_date': relative_seconds_to_datetime(response_json['expires_in'])
        })
        return response_json

    @property
    def auth_header(self) -> dict:
        return {}

    def authorize_url(self, scope: str, redirect_uri: str) -> str:
        """
        The authorize URL in PagerDuty that the end user will visit to authorize the app

        :param scope:
            Scope of the OAuth grant requested
        :param redirect_uri:
            The redirect URI in the application that receives the authorization code
            through client redirect from PagerDuty
        :returns:
            The formatted authorize URL.
        """
        return self.get_authorize_url(
            self.client_id,
            scope,
            redirect_uri
        )

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        if not (isinstance(api_key, str) and api_key):
            raise ValueError("Client secret must be a non-empty string.")
        self._api_key = api_key

    @classmethod
    def get_authorize_url(cls, client_id: str, scope: str, redirect_uri: str) -> str:
        """
        Generate an authorize URL.

        This method can be called directly to circumvent the need to produce a client
        secret that is otherwise required to instantiate an object.

        This is the URL that the user initially visits in the application to authorize
        the application, which will ultimately redirect the user to ``redirect_uri`` but
        with the authorization code.

        :param client_id:
            Client ID of the application
        :param scope:
            Scope of the OAuth grant requested
        :param redirect_uri:
            The redirect URI in the application that receives the authorization code
            through client redirect from PagerDuty
        :returns:
            The formatted authorize URL.
        """
        return cls.url + '/oauth/authorize?'+ urllib.parse.urlencode([
            ('client_id', client_id),
            ('redirect_uri', redirect_uri),
            ('response_type', 'code'),
            ('scope', scope)
        ])

    def get_new_token(self, **kw) -> dict:
        """
        Make a token request.

        There should not be any need to call this method directly. Each of the supported
        types of token exchange requests are implemented in other methods:

        * :attr:`get_new_token_from_code`
        * :attr:`get_refreshed_token`
        * :attr:`get_scoped_app_token`

        :returns:
            The JSON response from ``identity.pagerduty.com`` as a dictionary after
            amending via :attr:`amended_auth_response`. It should contain a key
            ``access_token`` with the new token and ``expiration_date`` containing the
            date and time when the token will expire in ISO8601 format.
        """
        params = {
            "client_id": self.client_id,
            "client_secret": self.api_key
        }
        params.update(kw)
        return self.amended_auth_response(self.post(
            '/oauth/token',
            data = params,
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        ))

    def get_new_token_from_code(self, auth_code: str, scope: str, redirect_uri: str) \
            -> dict:
        """
        Exchange an authorization code granted by the user for an access token.

        :param auth_code:
            The authorization code received by the application at the redirect URI
            provided.
        :param scope:
            The scope of the authorization request.
        :redirect_uri:
            The redirect URI that was used in the authorization request.
        :returns:
            The JSON response from ``identity.pagerduty.com``, containing a key
            ``access_token`` with the new token, as a dict
        """
        return self.get_new_token(
            grant_type = 'authorization_code',
            code = auth_code,
            scope = scope,
            redirect_uri = redirect_uri
        )

    def get_refreshed_token(self, refresh_token: str) -> dict:
        """
        Obtain a new access token using a refresh token.

        :param refresh_token:
            The refresh token provided in the response of the original access token,
            i.e. in the dict returned by :attr:`get_new_token`
        :returns:
            The JSON response from ``identity.pagerduty.com``, containing a key
            ``access_token`` with the new token, as a dict
        """
        return self.get_new_token(
            grant_type = 'refresh_token',
            refresh_token = refresh_token
        )

    def get_scoped_app_token(self, scope: str):
        """
        Obtain a scoped app token.

        This can be used to grant a server-side app a scoped non-user application token.

        :param scope:
            The scope of the authorization request.
        :returns:
            The JSON response from ``identity.pagerduty.com``, containing a key
            ``access_token`` with the new token, as a dict
        """
        return self.get_new_token(
            grant_type = 'client_credentials',
            scope = scope
        )

    def refresh_client(self, access_token: str, refresh_token: str,
                expiration_date: str, base_url: str = 'https://api.pagerduty.com', **kw
            ) -> Tuple[RestApiV2Client, Optional[dict]]:
        """
        Instantiate and return a :class:`pagerduty.RestApiV2Client` client object

        Performs a token refresh if the current time is later than
        :attr:`early_refresh_buffer` seconds before the expiration date.

        :param access_token:
            The current REST API access token.
        :param refresh_token:
            The refresh token required to refresh the access token.
        :param expiration_date:
            The expiration date of the access token, formatted as an ISO8601 datetime
            string, including the timezone suffix as a UTC offset. The value contained
            in the ``expiration_date`` key of the amended response dictionary returned
            by any of the "get token" methods should be usable as this parameter.
        :param base_url:
            The value to use for the ``url`` attribute of the API client object.
        :param kw:
            Keyword arguments to pass to the constructor of the API client object.
        :returns:
            A tuple containing a :class:`pagerduty.RestApiV2Client` object as its first
            element and the the amended OAuth response if a refresh was performed (and
            ``None`` otherwise) as its second element.
        """
        auth = None
        current_access_token = access_token
        if datetime_to_relative_seconds(expiration_date) < self.early_refresh_buffer:
            auth = self.get_refreshed_token(refresh_token)
            current_access_token = auth['access_token']
        client_kw = deepcopy(kw)
        client_kw.update({'auth_type': 'bearer'})
        client = RestApiV2Client(current_access_token, **client_kw)
        client.url = base_url
        return client, auth

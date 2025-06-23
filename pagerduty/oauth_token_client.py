import urllib.parse

from . api_client import ApiClient
from . common import successful_response
from . rest_api_v2_client import RestApiV2Client

class OAuthTokenClient(ApiClient):
    """
    Client with helpers for performing an OAuth exchange to obtain an access token.

    Requires `registering a PagerDuty App
    <https://developer.pagerduty.com/docs/register-an-app>`_ to obtain the necessary
    credentials, and must be used in the context of an OAuth2 authorization flow.

    For further details, refer to:

    - `OAuth Functionality <https://developer.pagerduty.com/docs/oauth-functionality>`_
    - `User OAuth Token via Code Grant <https://developer.pagerduty.com/docs/user-oauth-token-via-code-grant>`_
    - `User OAuth Token via PKCE <https://developer.pagerduty.com/docs/user-oauth-token-via-pkce>`_
    """

    url = 'https://identity.pagerduty.com'

    def __init__(self, client_id: str, client_secret: str, debug=False):
        """
        Create an OAuth token client

        :param client_id:
            The client ID provided when registering the application.
        :param client_secret:
            The secret associated with the application.
        :param redirect_uri:
            The redirect URI in the application that receives the authorization code
            through client redirect from PagerDuty
        """
        super(OAuthTokenClient, self).__init__(client_secret, debug=debug)
        self.client_id = client_id
        self.redirect_uri = redirect_uri

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
        """
        return self.get_authorize_url(
            self.client_id,
            scope,
            redirect_uri
        )

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
        return self.url + '/oauth/authorize?'+ urllib.parse.urlencode({
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope
        })

    def get_new_token(self, **kw) -> dict:
        """
        Make a token request.

        There should not be any need to call this method directly. Each of the supported
        types of token exchange requests are implemented in other methods:

        * :attr:`get_new_token_from_code`
        * :attr:`get_refreshed_token`
        * :attr:`get_scoped_app_token`

        :returns:
            The JSON response from ``identity.pagerduty.com``, containing a key
            ``access_token`` with the new token, as a dict
        """
        params = {
            "client_id": self.client_id,
            "client_secret": self.api_key
        }
        params.update(kw)
        return successful_response(self.post(
            '/oauth/token',
            data = params,
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )).json()

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
            The redirect URI to be used in the authorization request.
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
        )).json()

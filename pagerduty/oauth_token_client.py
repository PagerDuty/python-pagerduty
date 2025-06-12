import urllib.parse

from . api_client import ApiClient
from . common import successful_response
from . rest_api_v2_client import RestApiV2Client

class OAuthTokenClient(ApiClient):
    """
    Client with helpers for performing an OAuth exchange to obtaining an access token.

    Requires `registering a PagerDuty App
    <https://developer.pagerduty.com/docs/register-an-app>`_ to obtain the necessary
    credentials, and must be used in the context of an OAuth2 authorization flow.

    For further details, refer to:

    - `OAuth Functionality <https://developer.pagerduty.com/docs/oauth-functionality>`_
    - `User OAuth Token via Code Grant <https://developer.pagerduty.com/docs/user-oauth-token-via-code-grant>`_
    """

    url = 'https://identity.pagerduty.com'

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str,
            scope: str, debug=False):
        """
        Create an OAuth token client

        :param client_id:
            The client ID provided when registering the application.
        :param client_secret:
            The secret associated with the application.
        :param redirect_uri:
            The redirect URI in the application that receives the authorization code
            through client redirect from PagerDuty
        :param scope:
            The scope of the token grant to request.
        """
        super(OAuthTokenClient, self).__init__(client_secret, debug=debug)
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.scope = scope

    @property
    def auth_header(self) -> dict:
        return {}

    @property
    def authorize_url(self):
        """
        The authorize URL in PagerDuty that the end user will visit to authorize the app
        """
        self.get_authorize_url(
            self.client_id,
            self.redirect_uri,
            self.scope
        )

    @api_key.setter
    def api_key(self, api_key: str):
        if not (isinstance(api_key, str) and api_key):
            raise ValueError("Client secret must be a non-empty string.")
        self._api_key = api_key

    @classmethod
    def get_authorize_url(cls, client_id: str, redirect_uri: str, scope: str) -> str:
        """
        Generate an authorize URL.

        This method can be called directly to circumvent the need to produce a client
        secret that is otherwise required to instantiate an object.

        This is the URL that the user initially visits in the application to authorize
        the application, which will ultimately redirect the user to ``redirect_uri`` but
        with the authorization code.

        :param client_id:
            Client ID of the application
        :param redirect_uri:
            The redirect URI in the application that receives the authorization code
            through client redirect from PagerDuty
        :param scope:
            Scope of the OAuth gratn requested
        """
        return self.url + '/oauth/authorize?'+ urllib.parse.urlencode({
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope
        })

    def get_new_token(self, auth_code: str) -> dict:
        """
        Exchange an authorization code granted by the PagerDuty user for an access token

        :param auth_code:
            The authorization code received by the application at the redirect URI
            provided.
        :returns:
            The JSON response from ``identity.pagerduty.com`` as a dict
        """
        return successful_response(self.post(
            '/oauth/token',
            data={
                "client_id": self.client_id,
                "client_secret": self.api_key,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )).json()

    def get_refreshed_token(self, refresh_token: str) -> dict:
        """
        Obtain a new access token using a refresh token.

        :param refresh_token:
            The refresh token provided in the response of the original access token,
            i.e. in the dict returned by :attr:`get_new_token`
        :returns:
            The JSON response from ``identity.pagerduty.com`` as a dict
        """
        return successful_response(self.post(
            '/oauth/token',
            data={
                "client_id": self.client_id,
                "client_secret": self.api_key,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )).json()

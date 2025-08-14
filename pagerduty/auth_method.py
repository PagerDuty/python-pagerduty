# Local
from logging import debug
from . version import __version__
from . common import last_4

class AuthMethod():

    def auth_header(self) -> dict:
        """
        Generates the header that will be used for authenticating with
        the PagerDuty API
        """
        raise NotImplementedError

    def trunc_key(self) -> str:
        """
        Returns a truncated version of the API key for display purposes.
        """
        raise NotImplementedError

class ApiKeyAuthMethod(AuthMethod):

    def __init__(self, api_key: str):
        """
        Authentication method using an API key.

        :param api_key:
            The API secret to use for authentication in HTTP requests
        :param debug:
            Sets :attr:`print_debug`. Set to ``True`` to enable verbose command line
            output.
        """
        self.api_key = api_key

    def auth_header(self) -> dict:
        return {"Authorization": f"Token token={self.api_key}"}

    def trunc_key(self):
        return last_4(self.api_key)

class OAuthTokenAuthMethod(AuthMethod):
    def __init__(self, oauth_token: str):
        """
        Authentication method using an OAuth token.

        :param oauth_token:
            A static OAuth token to use for authentication in HTTP requests
        """
        self.oauth_token = oauth_token

    def auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.oauth_token}"}

    def trunc_key(self):
        return last_4(self.oauth_token)

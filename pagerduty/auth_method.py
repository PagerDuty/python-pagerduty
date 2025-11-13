# Local
from . common import last_4

class AuthMethod():
    """
    An abstract class for authentication methods.

    **Design note:** we currently still implement our own interface for API authentication
    instead of making a custom ``httpx.AuthType`` (which would be more elegant and
    require less bespoke code) because some of our APIs' authorization methods require
    adding parameters to the body. Once the ``Request`` object has been instantiated,
    its body is already encoded based on the ``json`` keyword argument to its
    constructor. Therefore, it has no concept of "body parameters" that can be trivially
    updated in the scope of ``AuthType.auth_flow()``, unless we were to implement our
    own custom ``Request`` subclass that is aware of its body payload being a map-like
    object and rewrite the :attr:`pagerduty.ApiClient.request` method to prepare and
    send requests. Such a deep level of customization may make the client more brittle
    to upstream changes.

    :param secret:
        The API credential to be used for authentication.
    """

    def __init__(self, secret):
        self.secret = secret

    @property
    def auth_header(self) -> dict:
        """
        Generates the header that will be used for authenticating with
        the PagerDuty API
        """
        raise NotImplementedError

    @property
    def auth_param(self) -> dict:
        """
        Generates an authentication parameter to go into the body of the request.
        """
        raise NotImplementedError

    @property
    def secret(self):
        """
        Returns the API secret associated with the authentication method.
        """
        return self._secret

    @secret.setter
    def secret(self, secret):
        self._secret = secret

    @property
    def trunc_secret(self) -> str:
        """
        Returns a truncated version of the API credential for display purposes.
        """
        return last_4(self.secret)

class HeaderAuthMethod(AuthMethod):
    """
    Abstract base class for auth methods that authenticate using request headers.

    In this class, ``auth_param`` is defined such that it injects no parameters into the
    body of the request by default, leaving ``auth_header`` un-implemented.
    """

    @property
    def auth_param(self) -> dict:
        return {}

class BodyParameterAuthMethod(AuthMethod):
    """
    Abstract base class for auth methods that authenticate using a body parameter.

    In this class, ``auth_header`` is defined such that it adds no headers to the
    request, but it leaves ``auth_param`` un-implemented to require its implementation.
    """

    @property
    def auth_header(self) -> dict:
        return {}

class PassThruHeaderAuthMethod(HeaderAuthMethod):
    """
    Auth method that sets the ``Authorization`` header equal to ``secret``, verbatim.

    This is for use cases where an ``Authorization`` header must be passed through for
    authentication, i.e. in an API proxy or MCP server.
    """
    @property
    def auth_header(self) -> dict:
        return {"Authorization": self.secret}



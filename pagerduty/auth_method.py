# Local
from . version import __version__
from . common import last_4

class AuthMethod():
    """
    An abstract class for authentication methods.

    We implement our own interface instead of using the upstream library's interface for
    auth methods because it does not natively support all the different use cases needed
    for supporting all of PagerDuty's public APIs, i.e. the ``Bearer`` method, or
    placing the API credential into a parameter in the body of the request.
    """

    def __init__(self, secret):
        self._secret = secret

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
    def auth_header(self):
        return {}

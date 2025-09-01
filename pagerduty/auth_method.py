# Local
from . version import __version__
from . common import last_4

class AuthMethod():
    """
    An abstract class for authentication methods.
    """

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
from typing import Optional
import uuid

from .api_client import ApiClient
from .auth_method import AuthMethod
from .common import successful_response
from .errors import ServerHttpError


class McpApiClient(ApiClient):
    """
    Client class for the PagerDuty MCP API.

    For constructor arguments, see :class:`pagerduty.ApiClient`.

    Usage example:

    .. code-block:: python

        # Import and use OAuthTokenAuthMethod instead of TokenAuthMethod to use
        # an application OAuth token:
        from pagerduty import (
            McpApiClient,
            TokenAuthMethod
        )

        # Instantiate:
        client = McpApiClient(TokenAuthMethod(API_KEY))

        # Call a method and get the result:
        result = client.call('tools/list')['result']
    """

    def __init__(
            self,
            auth_method: AuthMethod,
            debug = False,
            base_url = None,
            **kw
        ):
        super(McpApiClient, self).__init__(
            auth_method,
            debug = debug,
            base_url = base_url,
            **kw
        )
        self.headers.update({"Accept": "application/json, text/event-stream"})

    def call(
        self, method: str, params: Optional[dict] = None, req_id=None
    ) -> dict:
        """
        Make a JSON-RPC request to the MCP API.

        :param method:
            The JSON-RPC method to invoke.
        :param params:
            The parameters to send to the RPC method.
        :param req_id:
            A unique ID to send with the request. A random UUID will be used if
            this argument is unspecified; the ID will then be passed back in
            the response.
        :returns:
            The JSON-decoded response body; it will be a dictionary containing
            a "result" key with the response data.
        """
        if not req_id:
            req_id = str(uuid.uuid4())
        body = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params:
            body["params"] = params
        response = successful_response(self.post("/mcp", json=body))
        response_body = response.json()
        if "result" not in response_body:
            raise ServerHttpError(
                "JSON-RPC response from PagerDuty did not include the "
                + 'expected "result" key.',
                response,
            )
        return response_body

    @property
    def default_base_url(self) -> str:
        return "https://mcp.pagerduty.com"

    @property
    def permitted_methods(self) -> tuple:
        return ("POST",)


__all__ = ["McpApiClient"]

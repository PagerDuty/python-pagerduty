from typing import Optional
import uuid

from . api_client import ApiClient
from . auth_method import AuthMethod
from . common import successful_response
from . rest_api_v2_base_client import (
    OAuthTokenAuthMethod,
    TokenAuthMethod
)

class McpApiClient(ApiClient):
    """
    API client for the PagerDuty MCP endpoint.

    Usage example:

    .. code-bloock:: python

        # Import OAuthTokenAuthMethod instead of TokenAuthMethod to use an OAuth token:
        from pagerduty.mcp_api_client import (
            McpApiClient,
            TokenAuthMethod
        )

        # Instantiate:
        auth_method = TokenAuthMethod(API_KEY)
        client = McpApiClient(auth_method)

        # Call a method and get the result:
        result = client.call('tools/list')['result']
    """

    url = 'https://mcp.pagerduty.com'

    def __init__(self, auth_method: AuthMethod, debug=False):
        super(McpApiClient, self).__init__(auth_method, debug=debug)
        self.headers.update({'Accept': 'application/json, text/event-stream'})

    def call(self, method: str, params: Optional[dict] = None, req_id = None) -> dict:
        """
        Make a JSON-RPC request to the MCP API.

        :param method:
            The JSON-RPC method to invoke.
        :param params:
            The parameters to send to the RPC method.
        :param req_id:
            A unique ID to send with the request. Will be a random UUID if unspecified.
        :returns:
            The JSON-decoded response body object, which should contain a "result" key.
        """
        if not req_id:
            req_id = str(uuid.uuid4())
        body = {
            'jsonrpc': '2.0',
            'id': req_id,
            'method': method,
        }
        if params:
            body['params'] = params
        return successful_response(self.post("/mcp", json=body)).json()

__all__ = [
    'McpApiClient',
    'OAuthTokenAuthMethod',
    'TokenAuthMethod'
]

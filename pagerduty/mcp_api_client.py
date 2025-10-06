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

        # Import OAuthTokenMethod instead of TokenAuthMethod to use an OAuth API token:
        from pagerduty.mcp_api_client import (
            McpApiClient,
            TokenAuthMethod
        )

        auth_method = TokenAuthMethod(API_KEY)
        client = McpApiClient(auth_method)
        result = client.call('tools/list')['result']
    """

    url = 'https://mcp.pagerduty.com'

    def call(self, method: str, params = None: Optional[dict], req_id=None) -> dict:
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
        return successful_response(self.post("/mcp", json = body).json()

__all__ = [
    'McpApiClient',
    'OAuthTokenAuthMethod',
    'TokenAuthMethod'
]

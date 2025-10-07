from typing import Optional
import uuid

from . api_client import ApiClient
from . auth_method import AuthMethod
from . common import successful_response
from . errors import HttpServerError
from . rest_api_v2_base_client import (
    OAuthTokenAuthMethod,
    TokenAuthMethod
)

class McpApiClient(ApiClient):
    """
    Client class for the PagerDuty MCP API

    Usage example:

    .. code-block:: python

        # Import and use OAuthTokenAuthMethod instead of TokenAuthMethod to use an
        # application OAuth token:
        from pagerduty import (
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
            A unique ID to send with the request. A random UUID will be used if this
            argument is unspecified; the ID will then be passed back in the response.
        :returns:
            The JSON-decoded response body; it will be a dictionary containing a
            "result" key with the response data.
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
        response = successful_response(self.post("/mcp", json=body))
        response_body = response.json()
        if 'result' not in response_body:
            raise HttpServerError('JSON-RPC response from PagerDuty did not include ' +
                'the expected "result" key.', response)
        return response_body

__all__ = [
    'McpApiClient'
]

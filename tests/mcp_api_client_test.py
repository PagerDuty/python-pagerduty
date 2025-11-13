import json
import unittest
from unittest.mock import patch

from mocks import Response
from pagerduty import ApiClient, McpApiClient, TokenAuthMethod


class McpApiClientTest(unittest.TestCase):
    @patch.object(ApiClient, "post")
    def test_call(self, post):
        post.return_value = Response(
            200,
            json.dumps(
                {"id": "42", "jsonrpc": "2.0", "result": {"foo": "bar"}}
            ),
        )
        auth = TokenAuthMethod("foo")
        client = McpApiClient(auth)
        r = client.call("tools/list", req_id="42")
        post.assert_called_once_with(
            "/mcp", json={"jsonrpc": "2.0", "id": "42", "method": "tools/list"}
        )

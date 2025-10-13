import json
import unittest
from unittest.mock import patch

import requests

from mocks import Response
from pagerduty import (
    ApiClient,
    ScimApiClient,
    TokenAuthMethod
)

class ScimApiClientTest(unittest.TestCase):

    @patch.object(ApiClient, 'get')
    def test_list_users(self, get):
        pass

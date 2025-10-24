import json
import unittest
import unittest.mock
from unittest.mock import patch

import httpx

from mocks import Response
from pagerduty import (
    ApiClient,
    ScimApiClient,
    TokenAuthMethod
)

class ScimApiClientTest(unittest.TestCase):

    @patch.object(ApiClient, 'get')
    def test_list_users(self, get):
        # Set up SCIM API client
        client = ScimApiClient(TokenAuthMethod('test-token'))

        # Mock responses for paginated results
        # First page response (2 users, total 5 users)
        first_response = Response(200, json.dumps({
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
            'totalResults': 5,
            'itemsPerPage': 2,
            'startIndex': 1,
            'Resources': [
                {'id': 'user1', 'userName': 'user1@example.com'},
                {'id': 'user2', 'userName': 'user2@example.com'}
            ]
        }))

        # Second page response (2 users)
        second_response = Response(200, json.dumps({
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
            'totalResults': 5,
            'itemsPerPage': 2,
            'startIndex': 3,
            'Resources': [
                {'id': 'user3', 'userName': 'user3@example.com'},
                {'id': 'user4', 'userName': 'user4@example.com'}
            ]
        }))

        # Third page response (1 user, last page)
        third_response = Response(200, json.dumps({
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
            'totalResults': 5,
            'itemsPerPage': 1,
            'startIndex': 5,
            'Resources': [
                {'id': 'user5', 'userName': 'user5@example.com'}
            ]
        }))

        # Configure mock to return different responses for each call
        get.side_effect = [first_response, second_response, third_response]

        # Call the method
        result = client.list_users(page_size=2)

        # Verify all users were returned
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0]['id'], 'user1')
        self.assertEqual(result[1]['id'], 'user2')
        self.assertEqual(result[2]['id'], 'user3')
        self.assertEqual(result[3]['id'], 'user4')
        self.assertEqual(result[4]['id'], 'user5')

        # Verify correct API calls were made
        expected_calls = [
            unittest.mock.call('/Users', params={'startIndex': 1, 'count': 2}),
            unittest.mock.call('/Users', params={'startIndex': 3, 'count': 2}),
            unittest.mock.call('/Users', params={'startIndex': 5, 'count': 2})
        ]
        get.assert_has_calls(expected_calls)
        self.assertEqual(get.call_count, 3)

    @patch.object(ApiClient, 'get')
    def test_list_users_with_filter(self, get):
        # Test with SCIM filter parameter
        client = ScimApiClient(TokenAuthMethod('test-token'))

        response = Response(200, json.dumps({
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
            'totalResults': 1,
            'itemsPerPage': 1,
            'startIndex': 1,
            'Resources': [
                {'id': 'filtered_user', 'userName': 'filtered@example.com'}
            ]
        }))

        get.return_value = response

        # Call with filter
        result = client.list_users(fltr='userName eq "filtered@example.com"')

        # Verify filter was passed correctly
        get.assert_called_once_with('/Users', params={
            'startIndex': 1,
            'count': 100,
            'filter': 'userName eq "filtered@example.com"'
        })
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 'filtered_user')

    @patch.object(ApiClient, 'get')
    def test_list_users_empty_results(self, get):
        # Test with no users returned
        client = ScimApiClient(TokenAuthMethod('test-token'))

        response = Response(200, json.dumps({
            'schemas': ['urn:ietf:params:scim:api:messages:2.0:ListResponse'],
            'totalResults': 0,
            'itemsPerPage': 0,
            'startIndex': 1,
            'Resources': []
        }))

        get.return_value = response

        result = client.list_users()

        self.assertEqual(len(result), 0)
        get.assert_called_once_with('/Users', params={'startIndex': 1, 'count': 100})

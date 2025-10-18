from unittest.mock import Mock, MagicMock, patch, call

from common_test import ClientTest
from mocks import Response

import pagerduty

EVENT_TIMESTAMP = '2020-03-25T00:00:00Z'

class EventsApiV2ClientTest(ClientTest):

    def test_send_event(self):
        client = pagerduty.EventsApiV2Client('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [
            Response(202, '{"dedup_key":"abc123"}'),
            Response(202, '{"dedup_key":"abc123"}'),
            Response(202, '{"dedup_key":"abc123"}')
        ]
        with patch.object(client, 'parent', new=parent):
            ddk = client.trigger('testing 123', 'triggered.from.pagerduty',
                custom_details={"this":"that"}, severity='warning',
                images=[{'url':'https://http.cat/502.jpg'}])
            self.assertEqual('abc123', ddk)
            self.assertEqual(
                'POST',
                parent.request.call_args[0][0])
            self.assertEqual(
                'https://events.pagerduty.com/v2/enqueue',
                parent.request.call_args[0][1])
            print(parent.request.call_args)
            self.assertDictContainsCaseInsensitiveSubset(
                {'Content-Type': 'application/json'},
                parent.request.call_args[1]['headers'])
            self.assertNotIn(
                'x-routing-key',
                parent.request.call_args[1]['headers'])
            self.assertEqual(
                {
                    'event_action':'trigger',
                    'routing_key':'routingkey',
                    'payload':{
                        'summary': 'testing 123',
                        'source': 'triggered.from.pagerduty',
                        'severity': 'warning',
                        'custom_details': {'this':'that'},
                    },
                    'images': [{'url':'https://http.cat/502.jpg'}]
                },
                parent.request.call_args[1]['json'])
            ddk = client.resolve('abc123')
            self.assertEqual(
                {
                    'event_action':'resolve',
                    'dedup_key':'abc123',
                    'routing_key':'routingkey',
                },
                parent.request.call_args[1]['json'])

            ddk = client.acknowledge('abc123')
            self.assertEqual(
                {
                    'event_action':'acknowledge',
                    'dedup_key':'abc123',
                    'routing_key':'routingkey',
                },
                parent.request.call_args[1]['json'])

    def test_send_explicit_event(self):
        # test sending an event by calling `post` directly as opposed to any of
        # the methods written into the client for sending events
        client = pagerduty.EventsApiV2Client('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [Response(202, '{"dedup_key":"abc123"}')]
        with patch.object(client, 'parent', new=parent):
            response = client.post('/v2/enqueue', json={
                'payload': {
                    'summary': 'testing 123',
                    'source': 'pagerduty integration',
                    'severity': 'critical'
                },
                'event_action': 'trigger'
            })
            json_sent = parent.request.call_args[1]['json']
            self.assertTrue('routing_key' in json_sent)
            self.assertEqual(json_sent['routing_key'], 'routingkey')

    @patch('pagerduty.EventsApiV2Client.event_timestamp', EVENT_TIMESTAMP)
    def test_submit_change_event(self):
        client = pagerduty.EventsApiV2Client('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        # The dedup key for change events is unused so we don't care about the response
        # schema, only that it is valid JSON:
        parent.request.side_effect = [ Response(202, '{}') ]
        with patch.object(client, 'parent', new=parent):
            self.assertEqual(
                client.submit(
                    'testing 123',
                    'triggered.from.pagerduty',
                    custom_details={"this":"that"},
                    links=[{'href':'https://http.cat/502.jpg'}],
                ),
                None
            )
            self.assertEqual(
                'POST',
                parent.request.call_args[0][0])
            self.assertEqual(
                'https://events.pagerduty.com/v2/change/enqueue',
                parent.request.call_args[0][1])
            self.assertDictContainsCaseInsensitiveSubset(
                {'Content-Type': 'application/json'},
                parent.request.call_args[1]['headers'])
            self.assertNotIn(
                'X-Routing-Key',
                parent.request.call_args[1]['headers'])
            self.assertEqual(
                {
                    'routing_key':'routingkey',
                    'payload':{
                        'summary': 'testing 123',
                        'timestamp': EVENT_TIMESTAMP,
                        'source': 'triggered.from.pagerduty',
                        'custom_details': {'this':'that'},
                    },
                    'links': [{'href':'https://http.cat/502.jpg'}]
                },
                parent.request.call_args[1]['json'])
        # Same as above but with a custom timestamp:
        client = pagerduty.EventsApiV2Client('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [ Response(202, '{}') ]
        with patch.object(client, 'parent', new=parent):
            custom_timestamp = '2023-06-26T00:00:00Z'
            self.assertEqual(
                    client.submit(
                    'testing 123',
                    'triggered.from.pagerduty',
                    custom_details={"this":"that"},
                    links=[{'href':'https://http.cat/502.jpg'}],
                    timestamp=custom_timestamp,
                ),
                None
            )
            self.assertEqual(
                parent.request.call_args[1]['json']['payload']['timestamp'],
                custom_timestamp
            )

    @patch('pagerduty.EventsApiV2Client.event_timestamp', EVENT_TIMESTAMP)
    def test_submit_lite_change_event(self):
        client = pagerduty.EventsApiV2Client('routingkey')
        parent = MagicMock()
        parent.request = MagicMock()
        parent.request.side_effect = [ Response(202, '{}') ]
        with patch.object(client, 'parent', new=parent):
            client.submit('testing 123')
            self.assertEqual(
                'POST',
                parent.request.call_args[0][0])
            self.assertEqual(
                'https://events.pagerduty.com/v2/change/enqueue',
                parent.request.call_args[0][1])
            self.assertDictContainsCaseInsensitiveSubset(
                {'Content-Type': 'application/json'},
                parent.request.call_args[1]['headers'])
            self.assertNotIn(
                'X-Routing-Key',
                parent.request.call_args[1]['headers'])
            self.assertEqual(
                {
                    'routing_key':'routingkey',
                    'payload':{
                        'summary': 'testing 123',
                        'timestamp': EVENT_TIMESTAMP,
                    }
                },
                parent.request.call_args[1]['json'])



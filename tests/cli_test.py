import unittest
from unittest.mock import Mock, MagicMock, patch, call

import pagerduty
from pagerduty import cli

class CliTest(unittest.TestCase):

    @patch.object(pagerduty.EventsApiV2Client, 'trigger')
    def test_trigger(self, trigger_method):
        cli.run([
            '-k', 'routing_key_here',
            '-i', 'dedup_key_here',
            '--description', 'description_here',
            '--source', 'source_here',
            'trigger'
        ])
        trigger_method.assert_called_once_with(
            'description_here', 'source_here', dedup_key='dedup_key_here'
        )

    @patch.object(pagerduty.EventsApiV2Client, 'acknowledge')
    def test_acknowledge(self, acknowledge_method):
        cli.run([
            '-k', 'routing_key_here',
            '-i', 'dedup_key_here',
            'acknowledge'
        ])
        acknowledge_method.assert_called_once_with('dedup_key_here')

    @patch.object(pagerduty.EventsApiV2Client, 'resolve')
    def test_resolve(self, resolve_method):
        cli.run([
            '-k', 'routing_key_here',
            '-i', 'dedup_key_here',
            'resolve'
        ])
        resolve_method.assert_called_once_with('dedup_key_here')


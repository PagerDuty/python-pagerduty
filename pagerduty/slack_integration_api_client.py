from typing import List

from . rest_api_v2_base_client import (
    CanonicalPath,
    RestApiV2BaseClient
)

CANONICAL_PATHS = [
    "/incidents/{incident_id}/dedicated_channel"
    "/incidents/{incident_id}/notification_channels"
]

ENTITY_WRAPPER_CONFIG = {
    # Slack Dedicated Channels
    "* /incidents/{incident_id}/dedicated_channel": "channel",

    # Slack Notification Channels
    "GET /incidents/{incident_id}/notification_channels": "channels",
    "POST /incidents/{incident_id}/notification_channels": None,
}

class SlackIntegrationApiClient(RestApiV2BaseClient):
    """
    Client for the PagerDuty Slack Integration API.

    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    This client provides an abstraction layer for all of the endpoints of the
    `PagerDuty Slack Integration API
    <https://developer.pagerduty.com/api-reference/56fee4184eabc-pager-duty-slack-integration-api>`_
    except for the "Slack Connections" features, which are supported by 
    :class:`pagerduty.SlackIntegrationConnectionsApiClient`.

    For constructor arguments, see :class:`pagerduty.RestApiV2BaseClient`.
    """

    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE')

    url = "https://api.pagerduty.com/integration-slack"

    def __init__(self, api_key: str, auth_type: str = 'token', debug: bool = False):
        super(SlackIntegrationApiClient, self).__init__(api_key, auth_type=auth_type,
            debug=debug)
        self.headers.update({
            'Accept': 'application/json',
        })

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG


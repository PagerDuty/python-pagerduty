from . rest_api_v2_base_client import RestApiV2BaseClient

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
    """

    permitted_Methods = ('GET', 'POST', 'PUT', 'DELETE')

    url = "https://api.pagerduty.com/integration-slack"

    @property
    def auth_header(self) -> dict:
        return {"Authorization": "Token token="+self.api_key}

    @property
    def canonical_paths(self) -> list[str]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG


from typing import List

from . rest_api_v2_base_client import (
    CanonicalPath,
    RestApiV2BaseClient
)

CANONICAL_PATHS = [
    "/workspaces/{slack_team_id}/connections",
    "/workspaces/{slack_team_id}/connections/{connection_id}"
]

ENTITY_WRAPPER_CONFIG = {
    # Slack Connections
    "GET /workspaces/{slack_team_id}/connections": "slack_connections",
    "POST /workspaces/{slack_team_id}/connections": "slack_connection",
    "PUT /workspaces/{slack_team_id}/connections/{connection_id}": "slack_connection",
}

class SlackIntegrationConnectionsApiClient(RestApiV2BaseClient):
    """
    Client for the PagerDuty Slack Integration API's "Connections" endpoints.

    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    This client provides an abstraction layer for the
    `PagerDuty Slack Integration API
    <https://developer.pagerduty.com/api-reference/56fee4184eabc-pager-duty-slack-integration-api>`_,
    specifically the "Connections" API endpoints, which use a different hostname in
    the base URL, ``app.pagerduty.com``, as opposed to ``api.pagerduty.com``.

    For constructor arguments, see :class:`pagerduty.RestApiV2BaseClient`.
    """

    permitted_methods = ('GET', 'POST', 'PUT', 'DELETE')

    url = "https://app.pagerduty.com/integration-slack"

    def __init__(self, api_key: str, auth_type: str = 'token', debug: bool = False):
        super(SlackIntegrationConnectionsApiClient, self).__init__(api_key,
            auth_type=auth_type, debug=debug)
        self.headers.update({
            'Accept': 'application/json',
        })

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

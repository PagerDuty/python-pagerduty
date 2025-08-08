from . rest_api_v2_like_client import RestApiV2LikeClient

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

class SlackIntegrationConnectionsApiClient(RestApiV2LikeClient):
    """
    Client for the PagerDuty Slack Integration API's "Connections" endpoints

    This client provides an abstraction layer for the
    `PagerDuty Slack Integration API
    <https://developer.pagerduty.com/api-reference/56fee4184eabc-pager-duty-slack-integration-api>
    `_, specifically the "Connections" API endpoints, which use a different hostname in
    the base URL, ``app.pagerduty.com``, as opposed to ``api.pagerduty.com``.
    """

    permitted_Methods = ('GET', 'POST', 'PUT', 'DELETE')

    url = "https://app.pagerduty.com/integration-slack"

    @property
    def auth_header(self) -> dict:
        return {"Authorization": "Token token="+self.api_key}

    @property
    def canonical_paths(self) -> list[str]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

from typing import List

from .rest_api_v2_base_client import CanonicalPath, RestApiV2BaseClient


CANONICAL_PATHS = [
    "/rules"
]

ENTITY_WRAPPER_CONFIG = {
    # The /rules endpoints follow classic conventions; the wrapper can be inferred.
    #
    # This dictionary was intentionally created and left empty so that it is
    # fewer steps to support antipatterns if they get added to this API in the
    # future.
}


class JiraServerIntegrationApiClient(RestApiV2BaseClient):
    """
    Client for the PagerDuty Jira Server Integration API.

    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    This client provides an abstraction layer for the `PagerDuty Jira Server
    Integration API
    <https://developer.pagerduty.com/api-reference/47fca619cb161-pager-duty-jira-server-integration-api>`_.

    Its documentation indicates that it only supports "Bearer" (OAuth-based)
    authentication and does not support the original token-style API
    authentication. For that reason, its constructor does not accept an
    "auth_type" argument, and it is assumed that the provided OAuth token was
    generated using an OAuth flow.

    :param access_token:
        OAuth access token (Bearer token) obtained via an OAuth flow
    :param jira_signature_token:
        Connected Jira instance signature token. This validates the connection
        between PagerDuty and a specific Jira instance.
    :param debug:
        Sets :attr:`pagerduty.ApiClient.print_debug`. Set to ``True`` to enable
        verbose command line output.
    """

    def __init__(
        self,
        access_token: str,
        jira_signature_token: str,
        debug: bool = False,
        base_url = None,
        **kw,
    ):
        super(JiraServerIntegrationApiClient, self).__init__(
            access_token,
            auth_type = "bearer",
            debug = debug,
            base_url = base_url,
            **kw
        )

        self.jira_signature_token = jira_signature_token
        self.headers.update(
            {
                "Accept": "application/json",
                "x-pagerduty-jira-signature": self.jira_signature_token,
            }
        )

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def default_base_url(self) -> str:
        return "https://app.pagerduty.com/integration-jira-service"

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

    @property
    def permitted_methods(self) -> tuple:
        return ("GET", "POST", "PUT", "DELETE")

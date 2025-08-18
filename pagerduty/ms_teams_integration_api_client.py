from typing import List

from . rest_api_v2_base_client import (
    CanonicalPath,
    RestApiV2BaseClient
)

CANONICAL_PATHS = [
    '/incidents/{incident_id}/meeting'
]

ENTITY_WRAPPER_CONFIG = {
    # The "create a meeting" endpoint follows classic conventions.
    #
    # This dictionary was intentionally created and left empty so that it is fewer steps
    # to support antipatterns if they get added to this API in the future.
}

class MsTeamsIntegrationApiClient(RestApiV2BaseClient):
    """
    Client for the PagerDuty Microsoft Teams Integration API.

    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    This client provides an abstraction layer for the `PagerDuty MS Teams Integration
    API
    <https://developer.pagerduty.com/api-reference/2a7de89c77dc8-pager-duty-ms-teams-integration-api>`_.

    Its documentation indicates that it only supports the original "Token" style
    authentication and does not support OAuth token ("Bearer") authentication. For that
    reason, its constructor does not accept an "auth_type" argument, and it is assumed
    that the provided API key was generated through the PagerDuty web UI.

    For constructor arguments, see :class:`pagerduty.ApiClient`.
    """

    permitted_methods = ('POST', )

    url = "https://api.pagerduty.com/integration-ms-teams"

    def __init__(self, api_key: str, debug: bool = False):
        super(MsTeamsIntegrationApiClient, self).__init__(api_key,
            auth_type='token', debug=debug)
        self.headers.update({
            'Accept': 'application/json',
        })

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

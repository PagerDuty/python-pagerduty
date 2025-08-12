from typing import List

from . rest_api_v2_base_client import (
    CanonicalPath,
    RestApiV2BaseClient
)

CANONICAL_PATHS = [
    '/accounts_mappings',
    '/accounts_mappings/{id}'
]

ENTITY_WRAPPER_CONFIG = {
    'GET /accounts_mappings/{id}': None
}

class JiraCloudIntegrationApiClient(RestApiV2BaseClient):
    """
    Client for the PagerDuty Jira Server Integration API.

    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    This client provides an abstraction layer for the `PagerDuty Jira Cloud Integration API
    <https://developer.pagerduty.com/api-reference/70ea43d07719f-pager-duty-jira-cloud-integration-api>`_.

    For constructor arguments, see :class:`pagerduty.RestApiV2BaseClient`.
    """

    permitted_methods = ('GET', )

    url = "https://api.pagerduty.com/integration-jira-cloud"

    def __init__(self, api_key: str, auth_type: str = 'token', debug: bool = False):
        super(JiraCloudIntegrationApiClient, self).__init__(api_key,
            auth_type=auth_type, debug=debug)
        self.headers.update({
            'Accept': 'application/json',
            # All requests in the reference and not just data-bearing create/update
            # methods have this header, so it should also be included in GET:
            'Content-Type': 'application/json'
        })

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

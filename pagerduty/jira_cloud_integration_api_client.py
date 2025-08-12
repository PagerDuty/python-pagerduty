from . rest_api_v2_base_client import RestApiV2BaseClient

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

    :param api_key:
        REST API access token to use for HTTP requests
    :param auth_type:
        The type of credential in use. If authenticating with an OAuth access
        token, this must be set to ``oauth2`` or ``bearer``. This will determine the
        format of ``Authorization`` header that is sent to the API in each request.
    :param debug:
        Sets :attr:`print_debug`. Set to True to enable verbose command line
        output.
    """

    permitted_methods = ('GET', )

    url = "https://api.pagerduty.com/integration-jira-cloud"

    def __init__(self, api_key: str, auth_type: str = 'token', debug: bool = False):
        super(JiraCloudIntegrationApiClient, self).__init__(api_key,
            auth_type=auth_type, debug=debug)
        self.headers.update({
            'Accept': 'application/json',
        })

    @property
    def canonical_paths(self) -> list[str]:
        return CANONICAL_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

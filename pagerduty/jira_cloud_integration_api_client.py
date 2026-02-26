from typing import List

from .rest_api_v2_base_client import CanonicalPath, RestApiV2BaseClient

# NOTE: This API client contains an antipattern, where the base URL begins
# after `api.pagerduty.com`, whereas the boldfaced font (indicating the
# canonical path) begins with "/integration-jira-cloud", i.e. for the "List account
# mappings" endpoint:
# https://developer.pagerduty.com/api-reference/5c25164c9df6c-list-account-mappings
#
# This is the opposite of the Jira Server Integration API where the common base
# node is considered part of the base URL. Technically, by definition, the
# canonical path should begin with "/integration-jira-cloud", but to save
# effort on the part of the end user, that common base node is counted as part
# of the base URL instead of paths.
#
# This may need to change if we want any sort of automation or
# configuration-based support of schema antipatterns in this API, because the
# API schema documentation will be based around the common base node of the
# path being part of the path. It will also need to change if there are
# inconsistencies in the first node of the path (which cannot be ruled out),
# i.e. if any endpoint within the API begins with something other than
# "/integration-jira-cloud".
#
# In the mean time, to avoid breaking changes, it has to be manually updated;
# the same could be said of every other separately-documented API outside of
# REST API v2 (RestApiV2Client) that follows many of the same rules. For now it
# is manageable without automation because those APIs are small.
CANONICAL_PATHS = [
    "/accounts_mappings",
    "/accounts_mappings/{id}",
    "/accounts_mappings/{id}/rules",
    "/accounts_mappings/{id}/rules/{rule_id}",
]

ENTITY_WRAPPER_CONFIG = {
    "GET /accounts_mappings/{id}": None,
    # "List rules" follows orthodox schema patterns and supports pagination;
    # all other nested API endpoints, i.e. create / read / update rule, do not.
    "POST /accounts_mappings/{id}/rules": None,
    "* /accounts_mappings/{id}/rules/{rule_id}": None,
}


class JiraCloudIntegrationApiClient(RestApiV2BaseClient):
    """
    Client for the PagerDuty Jira Server Integration API.

    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    This client provides an abstraction layer for the `PagerDuty Jira Cloud
    Integration API
    <https://developer.pagerduty.com/api-reference/70ea43d07719f-pager-duty-jira-cloud-integration-api>`_.

    For constructor arguments, see :class:`pagerduty.RestApiV2BaseClient`.
    """

    def __init__(
        self,
        api_key: str,
        auth_type: str = "token",
        debug: bool = False,
        base_url=None,
        **kw,
    ):
        super(JiraCloudIntegrationApiClient, self).__init__(
            api_key, auth_type=auth_type, debug=debug, base_url=base_url, **kw
        )
        self.headers.update(
            {
                "Accept": "application/json",
                # All requests in the reference and not just data-bearing create/update
                # methods have this header, so it should also be included in GET:
                "Content-Type": "application/json",
            }
        )

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def default_base_url(self) -> str:
        return "https://api.pagerduty.com/integration-jira-cloud"

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

    @property
    def permitted_methods(self) -> tuple:
        return ("GET", "POST", "PUT", "DELETE")

# Core
from copy import deepcopy
from datetime import (
    datetime,
    timezone
)
from sys import getrecursionlimit
from typing import Iterator, List, Optional
from warnings import warn

# PyPI
from requests import Response

# Local
from . common import (
    datetime_intervals,
    strftime,
    strptime
)
from . rest_api_v2_base_client import (
    ITERATION_LIMIT,
    CanonicalPath,
    RestApiV2BaseClient,
    auto_json,
    canonical_path as canonical_path_common,
    entity_wrappers as entity_wrappers_common,
    wrapped_entities
)

########################
### DEFAULT SETTINGS ###
########################

RECURSION_LIMIT = getrecursionlimit() // 2

ITER_HIST_RECURSION_WARNING_TEMPLATE = """RestApiV2Client.iter_history cannot continue
bisecting historical time intervals because {reason}, but the total number of results in
the current requested time sub-interval ({since_until}) still exceeds the hard limit for
classic pagination, {iteration_limit}. Results will be incomplete.{suggestion}
""".replace("\n", " ")

# List of canonical REST API paths
#
# Supporting a new API for entity wrapping will require adding its patterns to
# this list. If it doesn't follow standard naming conventions, it will also
# require one or more new entries in ENTITY_WRAPPER_CONFIG.
#
# To generate new definitions for CANONICAL_PATHS and
# CURSOR_BASED_PAGINATION_PATHS based on the API documentation's source code,
# use scripts/get_path_list/get_path_list.py

# BEGIN auto-generated content

CANONICAL_PATHS = [
    '/{entity_type}/{id}/change_tags',
    '/{entity_type}/{id}/tags',
    '/abilities',
    '/abilities/{id}',
    '/addons',
    '/addons/{id}',
    '/alert_grouping_settings',
    '/alert_grouping_settings/{id}',
    '/analytics/metrics/incidents/all',
    '/analytics/metrics/incidents/escalation_policies',
    '/analytics/metrics/incidents/escalation_policies/all',
    '/analytics/metrics/incidents/services',
    '/analytics/metrics/incidents/services/all',
    '/analytics/metrics/incidents/teams',
    '/analytics/metrics/incidents/teams/all',
    '/analytics/metrics/pd_advance_usage/features',
    '/analytics/metrics/responders/all',
    '/analytics/metrics/responders/teams',
    '/analytics/raw/incidents',
    '/analytics/raw/incidents/{id}',
    '/analytics/raw/incidents/{id}/responses',
    '/analytics/raw/responders/{responder_id}/incidents',
    '/audit/records',
    '/automation_actions/actions',
    '/automation_actions/actions/{id}',
    '/automation_actions/actions/{id}/invocations',
    '/automation_actions/actions/{id}/services',
    '/automation_actions/actions/{id}/services/{service_id}',
    '/automation_actions/actions/{id}/teams',
    '/automation_actions/actions/{id}/teams/{team_id}',
    '/automation_actions/invocations',
    '/automation_actions/invocations/{id}',
    '/automation_actions/runners',
    '/automation_actions/runners/{id}',
    '/automation_actions/runners/{id}/teams',
    '/automation_actions/runners/{id}/teams/{team_id}',
    '/business_services',
    '/business_services/{id}',
    '/business_services/{id}/account_subscription',
    '/business_services/{id}/subscribers',
    '/business_services/{id}/supporting_services/impacts',
    '/business_services/{id}/unsubscribe',
    '/business_services/impactors',
    '/business_services/impacts',
    '/business_services/priority_thresholds',
    '/change_events',
    '/change_events/{id}',
    '/escalation_policies',
    '/escalation_policies/{id}',
    '/escalation_policies/{id}/audit/records',
    '/event_orchestrations',
    '/event_orchestrations/{id}',
    '/event_orchestrations/{id}/integrations',
    '/event_orchestrations/{id}/integrations/{integration_id}',
    '/event_orchestrations/{id}/integrations/migration',
    '/event_orchestrations/{id}/global',
    '/event_orchestrations/{id}/router',
    '/event_orchestrations/{id}/unrouted',
    '/event_orchestrations/services/{service_id}',
    '/event_orchestrations/services/{service_id}/active',
    '/event_orchestrations/{id}/cache_variables',
    '/event_orchestrations/{id}/cache_variables/{cache_variable_id}',
    '/event_orchestrations/services/{service_id}/cache_variables',
    '/event_orchestrations/services/{service_id}/cache_variables/{cache_variable_id}',
    '/extension_schemas',
    '/extension_schemas/{id}',
    '/extensions',
    '/extensions/{id}',
    '/extensions/{id}/enable',
    '/incident_workflows',
    '/incident_workflows/{id}',
    '/incident_workflows/{id}/instances',
    '/incident_workflows/actions',
    '/incident_workflows/actions/{id}',
    '/incident_workflows/triggers',
    '/incident_workflows/triggers/{id}',
    '/incident_workflows/triggers/{id}/services',
    '/incident_workflows/triggers/{trigger_id}/services/{service_id}',
    '/incidents',
    '/incidents/{id}',
    '/incidents/{id}/alerts',
    '/incidents/{id}/alerts/{alert_id}',
    '/incidents/{id}/business_services/{business_service_id}/impacts',
    '/incidents/{id}/business_services/impacts',
    '/incidents/{id}/custom_fields/values',
    '/incidents/{id}/log_entries',
    '/incidents/{id}/merge',
    '/incidents/{id}/notes',
    '/incidents/{id}/outlier_incident',
    '/incidents/{id}/past_incidents',
    '/incidents/{id}/related_change_events',
    '/incidents/{id}/related_incidents',
    '/incidents/{id}/responder_requests',
    '/incidents/{id}/snooze',
    '/incidents/{id}/status_updates',
    '/incidents/{id}/status_updates/subscribers',
    '/incidents/{id}/status_updates/unsubscribe',
    '/incidents/count',
    '/incidents/custom_fields',
    '/incidents/custom_fields/{field_id}',
    '/incidents/custom_fields/{field_id}/field_options',
    '/incidents/custom_fields/{field_id}/field_options/{field_option_id}',
    '/license_allocations',
    '/licenses',
    '/log_entries',
    '/log_entries/{id}',
    '/log_entries/{id}/channel',
    '/maintenance_windows',
    '/maintenance_windows/{id}',
    '/notifications',
    '/oauth_delegations',
    '/oauth_delegations/revocation_requests/status',
    '/oncalls',
    '/paused_incident_reports/alerts',
    '/paused_incident_reports/counts',
    '/priorities',
    '/response_plays',
    '/response_plays/{id}',
    '/response_plays/{response_play_id}/run',
    '/rulesets',
    '/rulesets/{id}',
    '/rulesets/{id}/rules',
    '/rulesets/{id}/rules/{rule_id}',
    '/schedules',
    '/schedules/{id}',
    '/schedules/{id}/audit/records',
    '/schedules/{id}/overrides',
    '/schedules/{id}/overrides/{override_id}',
    '/schedules/{id}/users',
    '/schedules/preview',
    '/service_dependencies/associate',
    '/service_dependencies/business_services/{id}',
    '/service_dependencies/disassociate',
    '/service_dependencies/technical_services/{id}',
    '/services',
    '/services/{id}',
    '/services/{id}/audit/records',
    '/services/{id}/change_events',
    '/services/{id}/integrations',
    '/services/{id}/integrations/{integration_id}',
    '/services/{id}/rules',
    '/services/{id}/rules/convert',
    '/services/{id}/rules/{rule_id}',
    '/standards',
    '/standards/{id}',
    '/standards/scores/{resource_type}',
    '/standards/scores/{resource_type}/{id}',
    '/status_dashboards',
    '/status_dashboards/{id}',
    '/status_dashboards/{id}/service_impacts',
    '/status_dashboards/url_slugs/{url_slug}',
    '/status_dashboards/url_slugs/{url_slug}/service_impacts',
    '/status_pages',
    '/status_pages/{id}/impacts',
    '/status_pages/{id}/impacts/{impact_id}',
    '/status_pages/{id}/services',
    '/status_pages/{id}/services/{service_id}',
    '/status_pages/{id}/severities',
    '/status_pages/{id}/severities/{severity_id}',
    '/status_pages/{id}/statuses',
    '/status_pages/{id}/statuses/{status_id}',
    '/status_pages/{id}/posts',
    '/status_pages/{id}/posts/{post_id}',
    '/status_pages/{id}/posts/{post_id}/post_updates',
    '/status_pages/{id}/posts/{post_id}/post_updates/{post_update_id}',
    '/status_pages/{id}/posts/{post_id}/postmortem',
    '/status_pages/{id}/subscriptions',
    '/status_pages/{id}/subscriptions/{subscription_id}',
    '/tags',
    '/tags/{id}',
    '/tags/{id}/users',
    '/tags/{id}/teams',
    '/tags/{id}/escalation_policies',
    '/teams',
    '/teams/{id}',
    '/teams/{id}/audit/records',
    '/teams/{id}/escalation_policies/{escalation_policy_id}',
    '/teams/{id}/members',
    '/teams/{id}/notification_subscriptions',
    '/teams/{id}/notification_subscriptions/unsubscribe',
    '/teams/{id}/users/{user_id}',
    '/templates',
    '/templates/{id}',
    '/templates/{id}/render',
    '/templates/fields',
    '/users',
    '/users/{id}',
    '/users/{id}/audit/records',
    '/users/{id}/contact_methods',
    '/users/{id}/contact_methods/{contact_method_id}',
    '/users/{id}/license',
    '/users/{id}/notification_rules',
    '/users/{id}/notification_rules/{notification_rule_id}',
    '/users/{id}/notification_subscriptions',
    '/users/{id}/notification_subscriptions/unsubscribe',
    '/users/{id}/oncall_handoff_notification_rules',
    '/users/{id}/oncall_handoff_notification_rules/{oncall_handoff_notification_rule_id}',
    '/users/{id}/sessions',
    '/users/{id}/sessions/{type}/{session_id}',
    '/users/{id}/status_update_notification_rules',
    '/users/{id}/status_update_notification_rules/{status_update_notification_rule_id}',
    '/users/me',
    '/vendors',
    '/vendors/{id}',
    '/webhook_subscriptions',
    '/webhook_subscriptions/{id}',
    '/webhook_subscriptions/{id}/enable',
    '/webhook_subscriptions/{id}/ping',
    '/workflows/integrations',
    '/workflows/integrations/{id}',
    '/workflows/integrations/connections',
    '/workflows/integrations/{integration_id}/connections',
    '/workflows/integrations/{integration_id}/connections/{id}',
]

CURSOR_BASED_PAGINATION_PATHS = [
    '/audit/records',
    '/automation_actions/actions',
    '/automation_actions/runners',
    '/escalation_policies/{id}/audit/records',
    '/incident_workflows/actions',
    '/incident_workflows/triggers',
    '/schedules/{id}/audit/records',
    '/services/{id}/audit/records',
    '/teams/{id}/audit/records',
    '/users/{id}/audit/records',
    '/workflows/integrations',
    '/workflows/integrations/connections',
    '/workflows/integrations/{integration_id}/connections',
]

# END auto-generated content

HISTORICAL_RECORD_PATHS = [
    '/audit/records',
    '/change_events',
    '/escalation_policies/{id}/audit/records',
    '/incidents',
    '/log_entries',
    '/oncalls',
    '/schedules/{id}/audit/records',
    '/services/{id}/audit/records',
    '/teams/{id}/audit/records',
    '/users/{id}/audit/records'
]

ENTITY_WRAPPER_CONFIG = {
    # Abilities
    'GET /abilities/{id}': None,
    # Add-ons follows orthodox schema patterns
    # Alert grouping settings follows orthodox schema patterns
    # Analytics
    '* /analytics/metrics/incidents/all': None,
    '* /analytics/metrics/incidents/escalation_policies': None,
    '* /analytics/metrics/incidents/escalation_policies/all': None,
    '* /analytics/metrics/incidents/services': None,
    '* /analytics/metrics/incidents/services/all': None,
    '* /analytics/metrics/incidents/teams': None,
    '* /analytics/metrics/incidents/teams/all': None,
    '* /analytics/metrics/pd_advance_usage/features': None,
    '* /analytics/metrics/responders/all': None,
    '* /analytics/metrics/responders/teams': None,
    '* /analytics/raw/incidents': None,
    '* /analytics/raw/incidents/{id}': None,
    '* /analytics/raw/incidents/{id}/responses': None,

    # Automation Actions
    'POST /automation_actions/actions/{id}/invocations': (None,'invocation'),

    # Paused Incident Reports
    'GET /paused_incident_reports/alerts': 'paused_incident_reporting_counts',
    'GET /paused_incident_reports/counts': 'paused_incident_reporting_counts',

    # Business Services
    '* /business_services/{id}/account_subscription': None,
    'POST /business_services/{id}/subscribers': ('subscribers', 'subscriptions'),
    'POST /business_services/{id}/unsubscribe': ('subscribers', None),
    '* /business_services/priority_thresholds': None,
    'GET /business_services/impacts': 'services',
    'GET /business_services/{id}/supporting_services/impacts': 'services',

    # Change Events
    'POST /change_events': None, # why not just use EventsApiV2Client?
    'GET /incidents/{id}/related_change_events': 'change_events',

    # Event Orchestrations
    '* /event_orchestrations': 'orchestrations',
    '* /event_orchestrations/services/{id}': 'orchestration_path',
    '* /event_orchestrations/services/{id}/active': None,
    '* /event_orchestrations/{id}': 'orchestration',
    '* /event_orchestrations/{id}/global': 'orchestration_path',
    '* /event_orchestrations/{id}/integrations/migration': None,
    '* /event_orchestrations/{id}/router': 'orchestration_path',
    '* /event_orchestrations/{id}/unrouted': 'orchestration_path',

    # Extensions
    'POST /extensions/{id}/enable': (None, 'extension'),

    # Incidents
    'PUT /incidents/{id}/merge': ('source_incidents', 'incident'),
    'POST /incidents/{id}/responder_requests': (None, 'responder_request'),
    'POST /incidents/{id}/snooze': (None, 'incident'),
    'POST /incidents/{id}/status_updates': (None, 'status_update'),
    'POST /incidents/{id}/status_updates/subscribers': ('subscribers', 'subscriptions'),
    'POST /incidents/{id}/status_updates/unsubscribe': ('subscribers', None),
    'GET /incidents/{id}/business_services/impacts': 'services',
    'PUT /incidents/{id}/business_services/{business_service_id}/impacts': None,
    '* /incidents/{id}/custom_fields/values': 'custom_fields',
    'POST /incidents/{id}/responder_requests': None,

    # Incident Custom Fields
    '* /incidents/custom_fields': ('field', 'fields'),
    '* /incidents/custom_fields/{field_id}': 'field',

    # Incident Types
    # TODO: Update after this is GA and no longer early-access (for now we are manually
    # excluding the canonical paths in the update)

    # Incident Workflows
    'POST /incident_workflows/{id}/instances': 'incident_workflow_instance',
    'POST /incident_workflows/triggers/{id}/services': ('service', 'trigger'),

    # Response Plays
    'POST /response_plays/{response_play_id}/run': None, # (deprecated)

    # Schedules
    'POST /schedules/{id}/overrides': ('overrides', None),

    # Service Dependencies
    'POST /service_dependencies/associate': 'relationships',

    # Webhooks
    'POST /webhook_subscriptions/{id}/enable': (None, 'webhook_subscription'),
    'POST /webhook_subscriptions/{id}/ping': None,

    # Status Dashboards
    'GET /status_dashboards/{id}/service_impacts': 'services',
    'GET /status_dashboards/url_slugs/{url_slug}': 'status_dashboard',
    'GET /status_dashboards/url_slugs/{url_slug}/service_impacts': 'services',

    # Status Pages
    # Adheres to orthodox API conventions / fully supported via inference from path

    # Tags
    'POST /{entity_type}/{id}/change_tags': None,

    # Teams
    'PUT /teams/{id}/escalation_policies/{escalation_policy_id}': None,
    'POST /teams/{id}/notification_subscriptions': ('subscribables', 'subscriptions'),
    'POST /teams/{id}/notification_subscriptions/unsubscribe': ('subscribables', None),
    'PUT /teams/{id}/users/{user_id}': None,
    'GET /teams/{id}/notification_subscriptions': 'subscriptions',

    # Templates
    'POST /templates/{id}/render': None,

    # Users
    '* /users/{id}/notification_subscriptions': ('subscribables', 'subscriptions'),
    'POST /users/{id}/notification_subscriptions/unsubscribe': ('subscribables', None),
    'GET /users/{id}/sessions': 'user_sessions',
    'GET /users/{id}/sessions/{type}/{session_id}': 'user_session',
    'GET /users/me': 'user',

    # Workflow Integrations
    # Adheres to orthodox API conventions / fully supported via inference from path

    # OAuth Delegations
    'GET /oauth_delegations/revocation_requests/status': None
}

################################
### REST API V2 URL HANDLING ###
################################

def canonical_path(base_url: str, url: str) -> str:
    """
    Return the REST API v2 canonical path for a given URL.

    This method should eventually be deprecated. For now it is included so that the
    changes to unit testing and the base namespace of the module don't have to change
    dramatically and can still use this wrapper.
    """
    return canonical_path_common(CANONICAL_PATHS, base_url, url)

###############################
### ENTITY WRAPPING HELPERS ###
###############################

def entity_wrappers(method: str, path: str) -> tuple:
    """
    Return the REST API v2 canonical path for a given URL.

    This method should eventually be deprecated. For now it is included so that the
    changes to unit testing and the base namespace of the module don't have to change
    dramatically and can still use this wrapper.
    """
    return entity_wrappers_common(ENTITY_WRAPPER_CONFIG, method, path)

################
# CLIENT CLASS #
################

class RestApiV2Client(RestApiV2BaseClient):
    """
    PagerDuty REST API v2 client class.

    Implements abstractions for the particular features of PagerDuty's REST API v2.
    Inherits from :class:`pagerduty.RestApiV2BaseClient`.

    :param api_key:
        REST API access token to use for HTTP requests.
    :param default_from:
        The default email address to use in the ``From`` header when making
        API calls using an account-level API access key.
    :param auth_type:
        The type of credential in use. If authenticating with an OAuth access
        token, this must be set to ``oauth2`` or ``bearer``. This will determine the
        format of the ``Authorization`` header that is sent to the API in each request.
    :param debug:
        Sets :attr:`pagerduty.ApiClient.print_debug`. Set to ``True`` to enable verbose
        command line output.
    """

    default_from = None
    """The default value to use as the ``From`` request header"""

    permitted_methods = ('GET', 'PATCH', 'POST', 'PUT', 'DELETE')

    url = 'https://api.pagerduty.com'
    """Base URL of the REST API"""

    def __init__(self, api_key: str, default_from: Optional[str] = None,
            auth_type: str = 'token', debug: bool = False):
        super(RestApiV2Client, self).__init__(api_key, auth_type=auth_type, debug=debug)
        self.default_from = default_from
        if default_from is not None:
            self.headers.update({
                'From': default_from
            })
        self.headers.update({
            'Accept': 'application/vnd.pagerduty+json;version=2',
        })

    def account_has_ability(self, ability: str) -> bool:
        """
        Test that the account has an ability.

        :param ability:
            The named ability, i.e. ``teams``.
        :returns:
            True or False based on whether the account has the named ability.
        """
        r = self.get(f"/abilities/{ability}")
        if r.status_code == 204:
            return True
        elif r.status_code == 402:
            return False
        elif r.status_code == 403:
            # Stop. Authorization failed. This is expected to be non-transient. This
            # may be added at a later time to ApiClient, i.e. to add a new default
            # action similar to HTTP 401. It would be a be a breaking change...
            raise HttpError(
                "Received 403 Forbidden response from the API. The identity "
                "associated with the credentials does not have permission to "
                "perform the requested action.", r)
        elif r.status_code == 404:
            raise HttpError(
                f"Invalid or unknown ability \"{ability}\"; API responded with status "
                "404 Not Found.", r)
        return False

    def after_set_api_key(self):
        self._subdomain = None

    @property
    def api_key_access(self) -> str:
        """
        Memoized API key access type getter.

        Will be "user" if the API key is a user-level token (all users should
        have permission to create an API key with the same permissions as they
        have in the PagerDuty web UI).

        If the API key in use is an account-level API token (as only a global
        administrator user can create), this property will be "account".
        """
        if not hasattr(self, '_api_key_access') or self._api_key_access is None:
            response = self.get('/users/me')
            if response.status_code == 400:
                message = try_decoding(response).get('error', '')
                if 'account-level access token' in message:
                    self._api_key_access = 'account'
                else:
                    self._api_key_access = None
                    self.log.error("Failed to obtain API key access level; "
                        "the API did not respond as expected.")
                    self.log.debug("Body = %s", truncate_text(response.text))
            else:
                self._api_key_access = 'user'
        return self._api_key_access

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        return CANONICAL_PATHS

    @property
    def cursor_based_pagination_paths(self) -> List[CanonicalPath]:
        return CURSOR_BASED_PAGINATION_PATHS

    @property
    def entity_wrapper_config(self) -> dict:
        return ENTITY_WRAPPER_CONFIG

    def find(self, resource: str, query: str, attribute: str = 'name',
            params: Optional[dict] = None) -> Optional[dict]:
        """
        Finds an object of a given resource type exactly matching a query.

        Works by querying a given resource index endpoint using the ``query`` parameter.
        To use this function on any given resource, the resource's index must support
        the ``query`` parameter; otherwise, the function may not work as expected. If
        the index ignores the parameter, for instance, this function will take much
        longer to return; results will not be constrained to those matching the query,
        and so every result in the index will be downloaded and compared against the
        query up until a matching result is found or all results have been checked.

        The comparison between the query and matching results is case-insenitive. When
        determining uniqueness, APIs are mostly case-insensitive, and therefore objects
        with similar characters but differing case can't even exist. All results (and
        the search query) are for this reason reduced pre-comparison to a common form
        (all-lowercase strings) so that case doesn't need to match in the query argument
        (which is also interpreted by the API as case-insensitive).

        If said behavior differs for a given API, i.e. the uniqueness constraint on a
        field is case-sensitive, it should still return the correct results because the
        search term sent to the index in the querystring is not lower-cased.

        :param resource:
            The name of the resource endpoint to query, i.e.
            ``escalation_policies``
        :param query:
            The string to query for in the the index.
        :param attribute:
            The property of each result to compare against the query value when
            searching for an exact match. By default it is ``name``, but when
            searching for user by email (for example) it can be set to ``email``
        :param params:
            Optional additional parameters to use when querying.
        :returns:
            The dictionary representation of the result, if found; ``None`` will
            be returned if there is no exact match result.
        """
        query_params = {}
        if params is not None:
            query_params.update(params)
        query_params.update({'query': query})
        simplify = lambda s: str(s).lower()
        search_term = simplify(query)
        equiv = lambda s: simplify(s[attribute]) == search_term
        obj_iter = self.iter_all(resource, params=query_params)
        return next(iter(filter(equiv, obj_iter)), None)

    def iter_alert_grouping_settings(self, service_ids: Optional[list] = None,
                limit: Optional[int] = None) -> Iterator[dict]:
        """
        Iterator for the contents of the "List alert grouping settings" endpoint.

        The API endpoint "GET /alert_grouping_settings" has its own unique method of
        pagination. This method provides an abstraction for it similar to what
        :attr:`iter_all` provides for endpoints that implement classic pagination.

        See:
        `List alert grouping settings <https://developer.pagerduty.com/api-reference/b9fe211cc2748-list-alert-grouping-settings>`_

        :param service_ids:
            A list of specific service IDs to which results will be constrained.
        :param limit:
            The number of results retrieved per page. By default, the value
            :attr:`default_page_size` will be used.
        :yields:
            Results from each page in the ``alert_grouping_settings`` response property.
        """
        more = True
        after = None
        page_size = self.default_page_size
        if limit is not None:
            page_size = limit
        while more:
            params = {'limit': page_size}
            if service_ids is not None:
                params['service_ids[]'] = service_ids
            if after is not None:
                params['after'] = after
            page = self.jget('/alert_grouping_settings', params=params)
            for result in page['alert_grouping_settings']:
                yield result
            after = page.get('after', None)
            more = after is not None

    def iter_analytics_raw_incidents(self, filters: dict, order: str = 'desc',
                order_by: str = 'created_at', limit: Optional[int] = None,
                time_zone: Optional[str] = None) -> Iterator[dict]:
        """
        Iterator for raw analytics data on multiple incidents.

        The API endpoint ``POST /analytics/raw/incidents`` has its own unique method of
        pagination. This method provides an abstraction for it similar to
        :attr:`iter_all`.

        See: 
        `Get raw data - multiple incidents <https://developer.pagerduty.com/api-reference/c2d493e995071-get-raw-data-multiple-incidents>`_

        :param filters:
            Dictionary representation of the required ``filters`` parameters.
        :param order:
            The order in which to sort results. Must be ``asc`` or ``desc``.
        :param order_by:
            The attribute of results by which to order results. Must be ``created_at``
            or ``seconds_to_resolve``.
        :param limit:
            The number of results to yield per page before requesting the next page. If
            unspecified, :attr:`default_page_size` will be used. The particular API
            endpoint permits values up to 1000.
        :yields:
            Entries of the ``data`` property in the response body from each page
        """
        page_size = self.default_page_size
        if limit is not None:
            page_size = limit
        more = True
        last = None
        while more:
            body = {
                'filters': filters,
                'order': order,
                'order_by': order_by,
                'limit': page_size
            }
            if time_zone is not None:
                body['time_zone'] = time_zone
            if last is not None:
                body['starting_after'] = last
            page = self.jpost('/analytics/raw/incidents', json=body)
            for result in page['data']:
                yield result
            last = page.get('last', None)
            more = page.get('more', False) and last is not None

    def iter_history(self, url: str, since: datetime, until: datetime,
            recursion_depth: int = 0, **kw) -> Iterator[dict]:
        """
        Yield all historical records from an endpoint in a given time interval.

        This method works around the limitation of classic pagination (see
        :attr:`pagerduty.rest_api_v2_base_client.ITERATION_LIMIT`) by recursively
        bisecting the initially-provided time interval until the total number of results
        in each sub-interval is less than the hard pagination limit.

        :param url:
            Index endpoint (API URL) from which to yield results. In the event that a
            cursor-based pagination endpoint is given, this method calls
            :attr:`iter_cursor` directly, as cursor-based pagination has no such
            limitation.
        :param since:
            The beginning of the time interval. This must be a non-naïve datetime object
            (i.e. it must be timezone-aware), in order to format the ``since`` parameter
            when transmitting it to the API such that it unambiguously takes the time
            zone into account. See: `datetime (Python documentation)
            <https://docs.python.org/3/library/datetime.html>`_
        :param until:
            The end of the time interval. A timezone-aware datetime object must be
            supplied for the same reason as for the ``since`` parameter.
        :param kw:
            Custom keyword arguments to pass to the iteration method. Note, if providing
            ``params`` in order to add query string parameters for filtering, the
            ``since`` and ``until`` keys (if present) will be ignored.
        :yields:
            All results from the resource collection API within the time range specified
            by ``since`` and ``until``.
        """
        path = self.canonical_path(url)
        since_until = {
            'since': strftime(since),
            'until': strftime(until)
        }
        iter_kw = deepcopy(kw)
        if path not in HISTORICAL_RECORD_PATHS:
            # Cannot continue; incompatible endpoint that doesn't accept since/until:
            raise UrlError(f"Method iter_history does not support {path}")
        elif path == '/oncalls':
            # Warn for this specific endpoint but continue:
            warn('iter_history may yield duplicate results when used with /oncalls')
        elif path in self.cursor_based_pagination_paths:
            # Short-circuit to iter_cursor:
            iter_kw.setdefault('params', {})
            iter_kw['params'].update(since_until)
            return self.iter_cursor(url, **iter_kw)
        # Obtain the total number of records for the interval:
        query_params = kw.get('params', {})
        query_params.update(since_until)
        total = self.get_total(url, params=query_params)

        no_results = total == 0
        can_fully_paginate = total <= ITERATION_LIMIT
        min_interval_len = int((until - since).total_seconds()) == 1
        stop_recursion = recursion_depth >= RECURSION_LIMIT
        if no_results:
            # Nothing to be done for this interval
            pass
        elif can_fully_paginate or min_interval_len or stop_recursion:
            # Do not subdivide any further; it is either not necessary or not feasible.
            if not can_fully_paginate:
                # Issue a warning log message
                if stop_recursion:
                    reason = 'the recursion depth limit has been reached'
                    suggestion = ' To avoid this issue, try requesting a smaller ' \
                        'initial time interval.'
                elif min_interval_len:
                    reason = 'the time interval is already the minimum length (1s)'
                    # In practice, this scenario can only happen when PagerDuty ingests
                    # and processes, for a single account, >10k alert history events per
                    # second (to use `/log_entries` as an example). There is
                    # unfortunately nothing more that can be done in this case.
                    suggestion = ''
                self.log.warning(ITER_HIST_RECURSION_WARNING_TEMPLATE.format(
                    reason = reason,
                    since_until = str(since_until),
                    iteration_limit = ITERATION_LIMIT,
                    suggestion = suggestion
                ))
            iter_kw.setdefault('params', {})
            iter_kw['params'].update(since_until)
            for item in self.iter_all(url, **iter_kw):
                yield item
        else:
            # If total exceeds maximum, bisect the time window and recurse:
            iter_kw['recursion_depth'] = recursion_depth + 1
            for (sub_since, sub_until) in datetime_intervals(since, until, n=2):
                for item in self.iter_history(url, sub_since, sub_until, **iter_kw):
                    yield item

    def iter_incident_notes(self, incident_id: Optional[str] = None, **kw) \
            -> Iterator[dict]:
        """
        Iterator for incident notes.

        This is a filtered iterator for log entries of type ``annotate_log_entry``.

        :param incident_id:
            Optionally, request log entries for a specific incident. If included, the
            ``team_ids[]`` query parameter will be removed and ignored.
        :param kw:
            Custom keyword arguments to send to :attr:`iter_all`.
        :yields:
            Incident note log entries as dictionary objects
        """
        my_kw = deepcopy(kw)
        my_kw.setdefault('params', {})
        url = '/log_entries'
        if incident_id is not None:
            url = f"/incidents/{incident_id}/log_entries"
            # The teams filter is irrelevant for a specific incident's log entries, so
            # it must be removed if present:
            for key in ('team_ids', 'team_ids[]'):
                if 'params' in my_kw and key in my_kw['params']:
                    self.log.warn(
                        f"iter_incident_notes: query parameter \"{key}\" will be "
                        "ignored because argument incident_id was specified"
                    )
                    del(my_kw['params'][key])
        return iter(filter(
            lambda ile: ile['type'] == 'annotate_log_entry',
            self.iter_all(url, **my_kw)
        ))

    def normalize_params(self, params: dict) -> dict:
        """
        Modify the user-supplied parameters to ease implementation

        Current behavior:

        * If a parameter's value is of type list, and the parameter name does
          not already end in "[]", then the square brackets are appended to keep
          in line with the requirement that all set filters' parameter names end
          in "[]".

        :returns:
            The query parameters after modification
        """
        updated_params = {}
        for param, value in params.items():
            if type(value) is list and not param.endswith('[]'):
                updated_params[param+'[]'] = value
            else:
                updated_params[param] = value
        return updated_params

    def persist(self, resource: str, attr: str, values: dict, update: bool = False) \
            -> dict:
        """
        Finds or creates and returns a resource with a matching attribute

        Given a resource name, an attribute to use as an idempotency key and a
        set of attribute:value pairs as a dict, create a resource with the
        specified attributes if it doesn't exist already and return the resource
        persisted via the API (whether or not it already existed).

        :param resource:
            The URL to use when creating the new resource or searching for an
            existing one. The underlying AP must support entity wrapping to use
            this method with it.
        :param attr:
            Name of the attribute to use as the idempotency key. For instance,
            "email" when the resource is "users" will not create the user if a
            user with the email address given in ``values`` already exists.
        :param values:
            The content of the resource to be created, if it does not already
            exist. This must contain an item with a key that is the same as the
            ``attr`` argument.
        :param update:
            (New in 4.4.0) If set to True, any existing resource will be updated
            with the values supplied.
        """
        if attr not in values:
            raise ValueError("Argument `values` must contain a key equal "
                "to the `attr` argument (expected idempotency key: '%s')."%attr)
        existing = self.find(resource, values[attr], attribute=attr)
        if existing:
            if update:
                original = {}
                original.update(existing)
                existing.update(values)
                if original != existing:
                    existing = self.rput(existing, json=existing)
            return existing
        else:
            return self.rpost(resource, json=values)

    @wrapped_entities
    def rpatch(self, path: str, **kw) -> dict:
        """
        Wrapped-entity-aware PATCH function.

        Currently the only API endpoint that uses or supports this method is "Update
        Workflow Integration Connection": ``PATCH
        /workflows/integrations/{integration_id}/connections/{id}``

        It cannot use the :attr:`resource_url` decorator because the schema in that case
        has no ``self`` property, and so the URL or path must be supplied.

        :param path:
            The URL to be requested
        :param kw:
            Keyword arguments to send to the request function, i.e. ``params``
        :returns:
            The API response after JSON-decoding and unwrapping
        """
        return self.patch(path, **kw)

    @property
    def subdomain(self) -> str:
        """
        Subdomain of the PagerDuty account of the API access token.
        """
        if not hasattr(self, '_subdomain') or self._subdomain is None:
            try:
                url = self.rget('users', params={'limit':1})[0]['html_url']
                self._subdomain = url.split('/')[2].split('.')[0]
            except Error as e:
                self.log.error("Failed to obtain subdomain; encountered error.")
                self._subdomain = None
                raise e
        return self._subdomain

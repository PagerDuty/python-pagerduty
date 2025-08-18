from . version import __version__

from . common import (
    TEXT_LEN_LIMIT,
    TIMEOUT,
    deprecated_kwarg,
    http_error_message,
    last_4,
    normalize_url,
    plural_name,
    requires_success,
    singular_name,
    successful_response,
    truncate_text,
    try_decoding
)

from . api_client import ApiClient

from . events_api_v2_client import EventsApiV2Client

from . oauth_token_client import OAuthTokenClient

from . rest_api_v2_base_client import (
    ITERATION_LIMIT,
    RestApiV2BaseClient,
    auto_json,
    endpoint_matches,
    infer_entity_wrapper,
    is_path_param,
    resource_url,
    unwrap,
    wrapped_entities
)

from . rest_api_v2_client import (
    CANONICAL_PATHS,
    CURSOR_BASED_PAGINATION_PATHS,
    ENTITY_WRAPPER_CONFIG,
    RestApiV2Client,
    canonical_path,
    entity_wrappers
)

from . jira_cloud_integration_api_client import JiraCloudIntegrationApiClient
from . jira_server_integration_api_client import JiraServerIntegrationApiClient
from . ms_teams_integration_api_client import MsTeamsIntegrationApiClient
from . slack_integration_api_client import SlackIntegrationApiClient
from . slack_integration_connections_api_client import SlackIntegrationConnectionsApiClient

from . errors import (
    Error,
    HttpError,
    ServerHttpError,
    UrlError
)

# For backwards compatibility, __all__ currently includes all of the above. This should
# eventually be cleaned up so that it includes only the most-used interfaces, i.e.
# client classes. That could be done as a minor breaking change in a new future major
# version, i.e. it would break "from pagerduty import *" use cases, which would be an
# opportunity to lessen the impact of a future breaking change that ends the practice of
# importing the helper methods and module configuration globals.
__all__ = [
    'ApiClient',
    'CANONICAL_PATHS',
    'CURSOR_BASED_PAGINATION_PATHS',
    'ENTITY_WRAPPER_CONFIG',
    'Error',
    'EventsApiV2Client',
    'HttpError',
    'ITERATION_LIMIT',
    'JiraCloudIntegrationApiClient',
    'JiraServerIntegrationApiClient',
    'MsTeamsIntegrationApiClient',
    'OAuthTokenClient',
    'RestApiV2BaseClient',
    'RestApiV2Client',
    'ServerHttpError',
    'SlackIntegrationApiClient',
    'SlackIntegrationConnectionsApiClient',
    'TEXT_LEN_LIMIT',
    'TIMEOUT',
    'UrlError',
    'auto_json',
    'canonical_path',
    'deprecated_kwarg',
    'endpoint_matches',
    'entity_wrappers',
    'http_error_message',
    'infer_entity_wrapper',
    'is_path_param',
    'last_4',
    'normalize_url',
    'plural_name',
    'requires_success',
    'resource_url',
    'singular_name',
    'successful_response',
    'truncate_text',
    'try_decoding',
    'unwrap',
    'wrapped_entities',
]

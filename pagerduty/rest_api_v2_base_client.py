# Core
from copy import deepcopy
from datetime import (
    datetime,
    timezone
)
from sys import getrecursionlimit
from typing import Iterator, List, Optional, Tuple, Union
from warnings import warn

# PyPI
from requests import Response

# Local
from . api_client import (
    ApiClient,
    normalize_url
)

from . common import (
    requires_success,
    singular_name,
    successful_response,
    truncate_text,
    try_decoding,
)
from . errors import (
    ServerHttpError,
    UrlError
)

#######################
### CLIENT DEFAULTS ###
#######################
ITERATION_LIMIT = 10000
"""
The maximum position of a result in classic pagination.

The offset plus limit parameter may not exceed this number. This is enforced server-side
and is not something the client may override. Rather, this value is reproduced in the
client to enable short-circuiting pagination, so that the client can avoid the HTTP 400
error that will result if the sum of the limit and offset parameters exceeds it.

See: `Pagination
<https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU4-pagination>`_.
"""

################################
### REST API V2 URL HANDLING ###
################################

CanonicalPath = str
"""
Canonical path type (alias of ``str``).

Canonical paths are the bold-typed portion of the path of the URL displayed in the API
reference at the top of each reference page for the given API endpoint. They are
interpreted as patterns, i.e. any part of the path enclosed in curly braces (as
determined by :attr:`pagerduty.rest_api_v2_base_client.is_path_param`) is interpreted as
a variable parameter versus a literal substring of the path.
"""

def canonical_path(paths: List[CanonicalPath], base_url: str, url: str) \
        -> CanonicalPath:
    """
    The canonical path from the API documentation corresponding to a URL.

    This method is used to identify and classify URLs according to which particular API
    endpoint within the client's corresponding API it belongs to, in order to account
    for any antipatterns that the endpoint might have.

    For examle, in 
    `List a user's contact methods
    <https://developer.pagerduty.com/api-reference/50d46c0eb020d-list-a-user-s-contact-methods>`_,
    the canonical path is ``/users/{id}/contact_methods``.

    :param paths:
        A list of paths supported by the API client. One example of this is
        ``pagerduty.rest_api_v2_client.CANONICAL_PATHS``.
    :param base_url:
        The base URL of the API
    :param url:
        A non-normalized URL (a path or full URL)
    :returns:
        The canonical API path corresponding to the URL.
    """
    full_url = normalize_url(base_url, url)
    # Starting with / after hostname before the query string:
    url_path = full_url.replace(base_url.rstrip('/'), '').split('?')[0]
    # Root node (blank) counts so we include it:
    n_nodes = url_path.count('/')
    # First winnow the list down to paths with the same number of nodes:
    patterns = list(filter(
        lambda p: p.count('/') == n_nodes,
        paths
    ))
    # Match against each node, skipping index zero because the root node always
    # matches, and using the adjusted index "j":
    for i, node in enumerate(url_path.split('/')[1:]):
        j = i+1
        patterns = list(filter(
            lambda p: p.split('/')[j] == node or is_path_param(p.split('/')[j]),
            patterns
        ))
        # Don't break early if len(patterns) == 1, but require an exact match...

    if len(patterns) == 0:
        raise UrlError(f"URL {url} does not match any canonical API path " \
            'supported by this client.')
    elif len(patterns) > 1:
        # If there's multiple matches but one matches exactly, return that.
        if url_path in patterns:
            return url_path

        # ...otherwise this is ambiguous.
        raise Exception(f"Ambiguous URL {url} matches more than one " \
            "canonical path pattern: "+', '.join(patterns)+'; this is likely ' \
            'a bug.')
    else:
        return patterns[0]

def endpoint_matches(endpoint_pattern: str, method: str, path: CanonicalPath) -> bool:
    """
    Whether an endpoint (method and canonical path) matches a given pattern.

    This is used by :attr:`pagerduty.rest_api_v2_base_client.entity_wrappers` for
    finding the appropriate entity wrapper configuration entry to use for a given HTTP
    method and API path.

    :param endpoint_pattern:
        The endpoint pattern in the form ``METHOD PATH`` where ``METHOD`` is the
        HTTP method in uppercase or ``*`` to match all methods, and ``PATH`` is
        a canonical API path.
    :param method:
        The HTTP method.
    :param path:
        The canonical API path
    :returns:
        True or False based on whether the pattern matches the endpoint
    """
    return (
        endpoint_pattern.startswith(method.upper()) \
            or endpoint_pattern.startswith('*')
    ) and endpoint_pattern.endswith(f" {path}")

def is_path_param(path_node: str) -> bool:
    """
    Whether a part of a canonical path represents a variable parameter

    :param path_node:
        The node (value between slashes) in the path
    :returns:
        True if the node represents a variable parameter, False if it is a fixed value
    """
    return path_node.startswith('{') and path_node.endswith('}')

###############################
### ENTITY WRAPPING HELPERS ###
###############################
EntityWrapper = str

EntityWrapping = Optional[EntityWrapper]
"""
Descriptive entity wrapping type.

If a string, it indicates that the entity is wrapped in a single property of the body of
the request or response named after the value of that string. If ``None``, it indicates
that entity wrapping is not enabled or should be ignored, i.e. send the user-supplied
request body in the API request or return the response body without any modification.
"""

EntityWrappingSpec = Tuple[EntityWrapping, EntityWrapping]
"""
Descriptive type that specifies how entity wrapping is configured for an API endoint.

The first member indicates the entity wrapping of the request body. The second indicates
the entity wrapping of the response body. The two may differ.
"""

def entity_wrappers(wrapper_config: dict, method: str, path: CanonicalPath) \
        -> EntityWrappingSpec:
    """
    Obtains entity wrapping information for a given endpoint (canonical path and method)

    The information about the API is dependency-injected as the ``wrapper_config``
    parameter. An example of such a dictionary object is
    ``pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG``.

    When trying to determine the entity wrapper name for a given API endpoint, the
    dictionary ``wrapper_config`` is first checked for keys that apply to a given
    request method and canonical API path based on a matching logic. If no keys are
    found that match, it is assumed that the API endpoint follows classic entity
    wrapping conventions, and the wrapper name can be inferred based on those
    conventions (see :attr:`pagerduty.rest_api_v2_base_client.infer_entity_wrapper`).
    Any new API that does not follow these conventions should therefore be given an
    entry in the ``wrapper_config`` dictionary in order to properly support it for
    entity wrapping.

    Each of the keys of should be a capitalized HTTP method (or ``*`` to match any
    method), followed by a space, followed by a canonical path. Each value is either a
    tuple with request and response body wrappers (if they differ), a string (if they
    are the same for both cases) or ``None`` (if wrapping is disabled and the data is to
    be marshaled or unmarshaled as-is). Values in tuples can also be None to denote that
    either the request or response is unwrapped.

    An endpoint, under the design logic of this client, is said to have entity wrapping
    if the body (request or response) has only one property containing the content
    requested or transmitted, apart from properties used for pagination. If there
    are any secondary content-bearing properties (other than those used for
    pagination), entity wrapping should be disabled to avoid discarding those
    properties from responses or preventing the use of those properties in request
    bodies.

    :param wrapper_config:
        A dictionary in which the entity wrapper antipattern configuration is specified.
    :param method:
        A HTTP method.
    :param path:
        A canonical API path.
    :returns:
        The entity wrapping specification.
    """
    m = method.upper()
    endpoint = "%s %s"%(m, path)
    match = list(filter(
        lambda k: endpoint_matches(k, m, path),
        wrapper_config.keys()
    ))

    if len(match) == 1:
        # Look up entity wrapping info from the global dictionary and validate:
        wrapper = wrapper_config[match[0]]
        invalid_config_error = 'Invalid entity wrapping configuration for ' \
                    f"{endpoint}: {wrapper}; this is most likely a bug."
        if wrapper is not None and type(wrapper) not in (tuple, str):
            raise Exception(invalid_config_error)
        elif wrapper is None or type(wrapper) is str:
            # Both request and response have the same wrapping at this endpoint.
            return (wrapper, wrapper)
        elif type(wrapper) is tuple and len(wrapper) == 2:
            # Endpoint uses different wrapping for request and response bodies.
            #
            # Both elements must be either str or None. The first element is the
            # request body wrapper and the second is the response body wrapper.
            # If a value is None, that indicates that the request or response
            # value should be encoded and decoded as-is without modifications.
            if False in [w is None or type(w) is str for w in wrapper]:
                # One or both is neither a string nor None, which is invalid:
                raise Exception(invalid_config_error)
            return wrapper
        else:
            # If not a tuple of length 2, or a string, or None, what are we doing here:
            raise Exception(invalid_config_error)
    elif len(match) == 0:
        # Nothing in entity wrapper config matches. In this case it is assumed
        # that the endpoint follows classic API patterns and the wrapper name
        # can be inferred from the URL and request method:
        wrapper = infer_entity_wrapper(method, path)
        return (wrapper, wrapper)
    else:
        matches_str = ', '.join(match)
        raise Exception(f"{endpoint} matches more than one pattern:" + \
            f"{matches_str}; this is most likely a bug.")

def infer_entity_wrapper(method: str, path: CanonicalPath) -> EntityWrapper:
    """
    Infer the entity wrapper name from the endpoint using orthodox patterns.

    This is based on patterns that are broadly applicable but not universal in
    the v2 REST API, where the wrapper name is predictable from the path and
    method. This is the default logic applied to determine the wrapper name
    based on the path if there is no explicit entity wrapping defined for the
    given path i.e. in :attr:`pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG` for
    :class:`pagerduty.RestApiV2Client`.

    :param method:
        The HTTP method
    :param path:
        A canonical API path i.e. from
        :attr:`pagerduty.rest_api_v2_client.CANONICAL_PATHS`
    """
    m = method.upper()
    path_nodes = path.split('/')
    if is_path_param(path_nodes[-1]):
        # Singular if it's an individual resource's URL for read/update/delete
        # (named similarly to the second to last node, as the last is its ID and
        # the second to last denotes the API resource collection it is part of):
        return singular_name(path_nodes[-2])
    elif m == 'POST':
        # Singular if creating a new resource by POSTing to the index containing
        # similar resources (named simiarly to the last path node):
        return singular_name(path_nodes[-1])
    else:
        # Plural if listing via GET to the index endpoint, or doing a multi-put:
        return path_nodes[-1]

def unwrap(response: Response, wrapper: EntityWrapping) -> Union[dict, list]:
    """
    Unwraps a wrapped entity from a HTTP response.

    :param response:
        The response object.
    :param wrapper:
        The entity wrapper (string), or None to skip unwrapping
    :returns:
        The value associated with the wrapper key in the JSON-decoded body of
        the response, which is expected to be a dictionary (map).
    """
    body = try_decoding(response)
    endpoint = "%s %s"%(response.request.method.upper(), response.request.url)
    if wrapper is not None:
        # There is a wrapped entity to unpack:
        bod_type = type(body)
        error_msg = f"Expected response body from {endpoint} after JSON-" \
            f"decoding to be a dictionary with a key \"{wrapper}\", but "
        if bod_type is dict:
            if wrapper in body:
                return body[wrapper]
            else:
                keys = truncate_text(', '.join(body.keys()))
                raise ServerHttpError(
                    error_msg + f"its keys are: {keys}",
                    response
                )
        else:
            raise ServerHttpError(
                error_msg + f"its type is {bod_type}.",
                response
            )
    else:
        # Wrapping is disabled for responses:
        return body

###########################
### FUNCTION DECORATORS ###
###########################

def auto_json(method: callable) -> callable:
    """
    Decorator to return the full response body object after decoding from JSON.

    Intended for use on functions that take a URL positional argument followed
    by keyword arguments and return a `requests.Response`_ object.

    The new return value is the JSON-decoded response body (``dict`` or ``list``).
    """
    doc = method.__doc__
    def call(self, url, **kw):
        return try_decoding(successful_response(method(self, url, **kw)))
    call.__doc__ = doc
    return call

def resource_url(method: callable) -> callable:
    """
    API call decorator that allows passing a resource dict as the path/URL

    Most resources returned by the API will contain a ``self`` attribute that is
    the URL of the resource itself.

    Using this decorator allows the implementer to pass either a URL/path or
    such a resource dictionary as the ``path`` argument, thus eliminating the
    need to re-construct the resource URL or hold it in a temporary variable.
    """
    doc = method.__doc__
    name = method.__name__
    def call(self, resource, **kw):
        url = resource
        if type(resource) is dict:
            if 'self' in resource: # passing an object
                url = resource['self']
            else:
                # Unsupported APIs for this feature:
                raise UrlError(f"The dict object passed to {name} in place of a URL "
                    "has no 'self' key and cannot be used in place of an API resource "
                    "path/URL.")
        elif type(resource) is not str:
            name = method.__name__
            raise UrlError(f"Value passed to {name} is not a str or dict with "
                "key 'self'")
        return method(self, url, **kw)
    call.__doc__ = doc
    return call

def wrapped_entities(method: callable) -> callable:
    """
    Decorator to automatically wrap request entities and unwrap response entities.

    Used for defining the ``r{method}`` functions, i.e.
    :attr:`pagerduty.RestApiV2BaseClient.rpost`. It makes the methods always return an
    object representing the resource entity in the response (whether wrapped in a
    root-level property or not) rather than the full response body, after JSON-decoding.
    When making a post / put request, and passing the ``json`` keyword argument to
    specify the content to be JSON-encoded as the body, that keyword argument can be
    either the to-be-wrapped content or the full body including the entity wrapper, and
    the ``json`` keyword argument will be normalized to include the wrapper.

    Methods using this decorator will raise a :class:`pagerduty.HttpError` with its
    ``response`` property being being the `requests.Response`_ object in the case of any
    error, so that the implementer can access it by catching the exception, and thus
    design their own custom logic around different types of error responses.

    :param method:
        Method being decorated. Must take one positional argument after ``self`` that is
        the URL/path to the resource, followed by keyword any number of keyword
        arguments, and must return an object of class `requests.Response`_, and be named
        after the HTTP method but with "r" prepended.
    :returns:
        A callable object; the reformed method
    """
    http_method = method.__name__.lstrip('r')
    doc = method.__doc__
    def call(self, url, **kw):
        pass_kw = deepcopy(kw) # Make a copy for modification
        path = self.canonical_path(url)
        endpoint = "%s %s"%(http_method.upper(), path)
        req_w, res_w = self.entity_wrappers(http_method, path)
        # Validate the abbreviated (or full) request payload, and automatically
        # wrap the request entity for the implementer if necessary:
        if req_w is not None and http_method in ('post', 'put') \
                and 'json' in pass_kw and req_w not in pass_kw['json']:
            pass_kw['json'] = {req_w: pass_kw['json']}

        # Make the request:
        r = successful_response(method(self, url, **pass_kw))

        # Unpack the response:
        return unwrap(r, res_w)
    call.__doc__ = doc
    return call


####################
### CLIENT CLASS ###
####################

class RestApiV2BaseClient(ApiClient):
    """
    Abstract base class for all API clients that support APIs similar to REST API v2

    This class implements some common features like numeric pagination that also appear
    and are supported to varying degrees outside of REST API v2.

    :param api_key:
        REST API access token to use for HTTP requests
    :param auth_type:
        The type of credential in use. If authenticating with an OAuth access
        token, this must be set to ``oauth2`` or ``bearer``. This will determine the
        format of the ``Authorization`` header that is sent to the API in each request.
    :param debug:
        Sets :attr:`pagerduty.ApiClient.print_debug`. Set to ``True`` to enable verbose
        command line output.
    """

    api_call_counts = None
    """A dict object recording the number of API calls per endpoint"""

    api_time = None
    """A dict object recording the total time of API calls to each endpoint"""

    default_page_size = 100
    """
    This will be the default number of results requested in each page when
    iterating/querying an index (the ``limit`` parameter).
    """

    def __init__(self, api_key: str, auth_type: str = 'token', debug: bool = False):
        self.api_call_counts = {}
        self.api_time = {}
        self.auth_type = auth_type
        super(RestApiV2BaseClient, self).__init__(api_key, debug=debug)

    @property
    def auth_type(self) -> str:
        """
        Defines the method of API authentication.

        This value determines how the Authorization header will be set. By default this
        is "token", which will result in the format ``Token token=<api_key>``.
        """
        return self._auth_type

    @auth_type.setter
    def auth_type(self, value: str):
        if value not in ('token', 'bearer', 'oauth2'):
            raise AttributeError("auth_type value must be \"token\" (default) "
                "or \"bearer\" or \"oauth\" to use OAuth2 authentication.")
        self._auth_type = value

    @property
    def auth_header(self) -> dict:
        if self.auth_type in ('bearer', 'oauth2'):
            return {"Authorization": "Bearer "+self.api_key}
        else:
            return {"Authorization": "Token token="+self.api_key}

    def canonical_path(self, url: str) -> CanonicalPath:
        """
        Return the canonical path of a URL for a particular API implementation.

        See: :attr:`pagerduty.rest_api_v2_base_client.canonical_path`

        :param url:
            The URL. Must be supported by the API.
        :returns:
            The canonical path corresponding to the URL.
        """
        return canonical_path(self.canonical_paths, self.url, url)

    @property
    def canonical_paths(self) -> List[CanonicalPath]:
        """
        List of canonical paths supported by the particular API client.

        Child classes that do not implement this method do not a-priori support any API
        endpoints for features that require entity wrapping, e.g. pagination.

        This value is used as the first argument to
        :attr:`pagerduty.rest_api_v2_base_client.canonical_path` from
        :attr:`pagerduty.RestApiV2BaseClient.canonical_path`.
        """
        return []

    @property
    def cursor_based_pagination_paths(self) -> List[CanonicalPath]:
        """
        List of paths known by the client to support standard cursor-based pagination.
        """
        return []

    def dict_all(self, path: str, by: str = 'id', **kw) -> dict:
        """
        Dictionary representation of all results from an index endpoint.

        With the exception of ``by``, all keyword arguments passed to this method are
        also passed to :attr:`iter_all`; see the documentation on that method for
        further details.

        :param path:
            The index endpoint URL to use.
        :param by:
            The attribute of each object to use for the key values of the dictionary.
            This is ``id`` by default. Please note, there is no uniqueness validation,
            so if you use an attribute that is not distinct for the data set, this
            function will omit some data in the results. If a property is named that
            the schema of the API requested does not have, this method will raise
            ``KeyError``.
        :param kw:
            Keyword arguments to pass to :attr:`iter_all`.
        :returns:
            A dictionary keyed by the values of the property of each result specified by
            the ``by`` parameter.
        """
        iterator = self.iter_all(path, **kw)
        return {obj[by]:obj for obj in iterator}

    @property
    def entity_wrapper_config(self) -> dict:
        """
        Entity wrapping antipattern specification for the given client.

        This dictionary object is sent to
        :attr:`pagerduty.rest_api_v2_base_client.entity_wrappers` when looking up how
        any given API endpoint wraps (or doesn't wrap) response and request entities;
        refer to the documentation on that method for further details.

        Child classes should implement this method and return appropriate configuration
        to cover all schema antipatterns in the APIs that they support. It is otherwise
        assumed that all endpoints in its corresponding API follow orthodox entity
        wrapping conventions, in which case the wrapper information can be inferred from
        the path itself.
        """
        return {}

    def entity_wrappers(self, http_method: str, path: CanonicalPath) \
            -> EntityWrappingSpec:
        """
        Get the entity-wrapper specification for any given API / API endpoint.

        See: :attr:`pagerduty.rest_api_v2_base_client.entity_wrappers`.

        :param http_method:
            The method of the request.
        :param path:
            The canonical API path of the request.
        :returns:
            The entity wrapper tuple to use in the given request.
        """
        return entity_wrappers(self.entity_wrapper_config, http_method, path)

    def get_total(self, url: str, params: Optional[dict] = None) -> int:
        """
        Gets the total count of records from a classic pagination index endpoint.

        :param url:
            The URL of the API endpoint to query
        :param params:
            An optional dictionary indicating additional parameters to send to the
            endpoint, i.e. filters, time range (``since`` and ``until``), etc. This may
            influence the total, i.e. if specifying a filter that matches a subset of
            possible results.
        :returns:
            The total number of results from the endpoint with the parameters given.
        """
        query_params = deepcopy(params)
        if query_params is None:
            query_params = {}
        query_params.update({
            'total': True,
            'limit': 1,
            'offset': 0
        })
        response = successful_response(self.get(url, params=query_params))
        response_json = try_decoding(response)
        if 'total' not in response_json:
            path = self.canonical_path(url)
            raise ServerHttpError(
                f"Response from endpoint GET {path} lacks a \"total\" property. This " \
                "may be because the endpoint does not support classic pagination, or " \
                "implements it incompletely or incorrectly.",
                response
            )
        return int(response_json['total'])

    def iter_all(self, url, params: Optional[dict] = None,
                page_size: Optional[int] = None, item_hook: Optional[callable] = None,
                total: bool = False) -> Iterator[dict]:
        """
        Iterator for the contents of an index endpoint or query.

        Automatically paginates and yields the results in each page, until all
        matching results have been yielded or a HTTP error response is received.

        If the URL to use supports cursor-based pagintation, then this will
        return :attr:`iter_cursor` with the same keyword arguments. Otherwise,
        it implements classic pagination, a.k.a. numeric pagination.

        Each yielded value is a dict object representing a result returned from
        the index. For example, if requesting the ``/users`` endpoint, each
        yielded value will be an entry of the ``users`` array property in the
        response.

        :param url:
            The index endpoint URL to use.
        :param params:
            Additional URL parameters to include.
        :param page_size:
            If set, the ``page_size`` argument will override the
            ``default_page_size`` parameter on the session and set the ``limit``
            parameter to a custom value (default is 100), altering the number of
            pagination results. The actual number of results in the response
            will still take precedence, if it differs; this parameter and
            ``default_page_size`` only dictate what is requested of the API.
        :param item_hook:
            Callable object that will be invoked for each item yielded, i.e. for
            printing progress. It will be called with three parameters: a dict
            representing a given result in the iteration, an int representing the number
            of the item in the series, and a value representing the total number of
            items in the series. If the total isn't knowable, i.e. the ``total``
            parameter is ``False`` or omitted, the value passed in for the third
            argument will be the string value ``"?"``.
        :param total:
            If True, the ``total`` parameter will be included in API calls, and
            the value for the third parameter to the item hook will be the total
            count of records that match the query. Leaving this as False confers
            a small performance advantage, as the API in this case does not have
            to compute the total count of results in the query.
        :yields:
            Results from each page of results.
        """
        # Get entity wrapping and validate that the URL being requested is
        # likely to support pagination:
        path = self.canonical_path(url)
        endpoint = f"GET {path}"

        # Short-circuit to cursor-based pagination if appropriate:
        if path in self.cursor_based_pagination_paths:
            return self.iter_cursor(url, params=params, page_size=page_size,
                item_hook=item_hook)

        nodes = path.split('/')
        if is_path_param(nodes[-1]):
            # NOTE: If this happens for a newer endpoint in REST API v2, and the final
            # path parameter is one of a fixed list of literal strings, the path might
            # need to be added to the EXPAND_PATHS dictionary in
            # scripts/get_path_list/get_path_list.py, after which CANONICAL_PATHS will
            # then need to be updated accordingly based on the new output of the script.
            raise UrlError(f"Path {path} (URL={url}) is formatted like an " \
                "individual resource versus a resource collection. It is " \
                "therefore assumed to not support pagination.")
        _, wrapper = self.entity_wrappers('GET', path)

        if wrapper is None:
            raise UrlError(f"Pagination is not supported for {endpoint}.")

        # Parameters to send:
        data = {
            'limit': (self.default_page_size, page_size)[int(bool(page_size))],
            'total': bool(total)
        }
        if isinstance(params, (dict, list)):
            # Override defaults with values given:
            data.update(dict(params))

        more = True
        offset = 0
        if params is not None:
            offset = int(params.get('offset', 0))
        n = 0
        while more:
            # Check the offset and limit:
            data['offset'] = offset
            highest_record_index = int(data['offset']) + int(data['limit'])
            if highest_record_index > ITERATION_LIMIT:
                iter_limit = '%d'%ITERATION_LIMIT
                warn(
                    f"Stopping iter_all on {endpoint} at " \
                    f"limit+offset={highest_record_index} " \
                    'as this exceeds the maximum permitted by the API ' \
                    f"({iter_limit}). The set of results may be incomplete."
                )
                return

            # Make the request and validate/unpack the response:
            r = successful_response(
                self.get(url, params=data.copy()),
                context='classic pagination'
            )
            body = try_decoding(r)
            results = unwrap(r, wrapper)

            # Validate and update pagination parameters
            #
            # Note, the number of the results in the actual response is always
            # the most appropriate amount to increment the offset by after
            # receiving each page. If this is the last page, pagination should
            # stop anyways because the ``more`` parameter should evaluate to
            # false.
            #
            # In short, the reasons why we don't trust the echoed ``limit``
            # value or stick to the limit requested and hope the server honors
            # it is that it could potentially result in skipping results or
            # yielding duplicates if there's a mismatch, or potentially issues
            # like PagerDuty/pdpyras#61
            data['limit'] = len(results)
            offset += data['limit']
            more = False
            if 'total' in body:
                total_count = body['total']
            else:
                total_count = '?'
            if 'more' in body:
                more = body['more']
            else:
                warn(
                    f"Response from endpoint GET {path} lacks a \"more\" property and "
                    "therefore does not support pagination. Only results from the "
                    "first request will be yielded. You can use \"rget\" with this "
                    "endpoint instead to avoid this warning."
                )

            # Perform per-page actions on the response data
            for result in results:
                n += 1
                # Call a callable object for each item, i.e. to print progress:
                if hasattr(item_hook, '__call__'):
                    item_hook(result, n, total_count)
                yield result

    def iter_cursor(self, url: str, params: Optional[dict] = None,
                item_hook: Optional[callable] = None,
                page_size: Optional[int] = None) -> Iterator[dict]:
        """
        Iterator for results from an endpoint using cursor-based pagination.

        :param url:
            The index endpoint URL to use.
        :param params:
            Query parameters to include in the request.
        :param item_hook:
            A callable object that accepts 3 positional arguments; see :attr:`iter_all`
            for details on how this argument is used.
        :param page_size:
            Number of results per page of results (the ``limit`` parameter). If
            unspecified, :attr:`default_page_size` will be used.
        :yields:
            Results from each page of results.
        """
        path = self.canonical_path(url)
        if path not in self.cursor_based_pagination_paths:
            raise UrlError(f"{path} does not support cursor-based pagination.")
        _, wrapper = self.entity_wrappers('GET', path)
        user_params = {
            'limit': (self.default_page_size, page_size)[int(bool(page_size))]
        }
        if isinstance(params, (dict, list)):
            # Override defaults with values given:
            user_params.update(dict(params))

        more = True
        next_cursor = None
        total = 0

        while more:
            # Update parameters and request a new page:
            if next_cursor:
                user_params.update({'cursor': next_cursor})
            r = successful_response(
                self.get(url, params=user_params),
                context='cursor-based pagination',
            )

            # Unpack and yield results
            body = try_decoding(r)
            results = unwrap(r, wrapper)
            for result in results:
                total += 1
                if hasattr(item_hook, '__call__'):
                    item_hook(result, total, '?')
                yield result

            # Advance to the next page
            next_cursor = body.get('next_cursor', None)
            more = bool(next_cursor)

    @resource_url
    @auto_json
    def jget(self, url: Union[str, dict], **kw) -> Union[dict, list]:
        """
        Performs a GET request, returning the JSON-decoded body as a dictionary
        """
        return self.get(url, **kw)

    @resource_url
    @auto_json
    def jpost(self, url: Union[str, dict], **kw) -> Union[dict, list]:
        """
        Performs a POST request, returning the JSON-decoded body as a dictionary
        """
        return self.post(url, **kw)

    @resource_url
    @auto_json
    def jput(self, url: Union[str, dict], **kw) -> Optional[Union[dict, list]]:
        """
        Performs a PUT request, returning the JSON-decoded body as a dictionary
        """
        return self.put(url, **kw)

    def list_all(self, url: str, **kw) -> list:
        """
        Returns a list of all objects from a given index endpoint.

        All keyword arguments passed to this function are also passed directly
        to :attr:`iter_all`; see the documentation on that method for details.

        :param url:
            The index endpoint URL to use.
        """
        return list(self.iter_all(url, **kw))

    def postprocess(self, response: Response, suffix: Optional[str] = None):
        """
        Records performance information / request metadata about the API call.

        :param response:
            The `requests.Response`_ object returned by the request method
        :param suffix:
            Optional suffix to append to the key
        :type method: str
        :type response: `requests.Response`_
        :type suffix: str or None
        """
        method = response.request.method.upper()
        url = response.request.url
        status = response.status_code
        request_date = response.headers.get('date', '(missing header)')
        request_id = response.headers.get('x-request-id', '(missing header)')
        request_time = response.elapsed.total_seconds()

        try:
            endpoint = "%s %s"%(method, self.canonical_path(url))
        except UrlError:
            # This is necessary so that profiling can also support using the
            # basic get / post / put / delete methods with APIs that are not yet
            # explicitly supported by inclusion in CANONICAL_PATHS.
            endpoint = "%s %s"%(method, url)
        self.api_call_counts.setdefault(endpoint, 0)
        self.api_time.setdefault(endpoint, 0.0)
        self.api_call_counts[endpoint] += 1
        self.api_time[endpoint] += request_time

        # Request ID / timestamp logging
        self.log.debug("Request completed: #method=%s|#url=%s|#status=%d|"
            "#x_request_id=%s|#date=%s|#wall_time_s=%g", method, url, status,
            request_id, request_date, request_time)
        if int(status/100) == 5:
            self.log.error("PagerDuty API server error (%d)! "
                "For additional diagnostics, contact PagerDuty support "
                "and reference x_request_id=%s / date=%s",
                status, request_id, request_date)

    @resource_url
    @requires_success
    def rdelete(self, resource: Union[str, dict], **kw) -> Response:
        """
        Delete a resource.

        :param resource:
            The path/URL to which to send the request, or a dict object
            representing an API resource that contains an item with key ``self``
            whose value is the URL of the resource.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.delete``
        """
        return self.delete(resource, **kw)

    @resource_url
    @wrapped_entities
    def rget(self, resource: Union[str, dict], **kw) -> Union[dict, list]:
        """
        Wrapped-entity-aware GET function.

        Retrieves a resource via GET and returns the wrapped entity in the
        response.

        :param resource:
            The path/URL to which to send the request, or a dict object
            representing an API resource that contains an item with key ``self``
            whose value is the URL of the resource.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.get``
        :returns:
            The API response after JSON-decoding and unwrapping
        """
        return self.get(resource, **kw)

    @wrapped_entities
    def rpost(self, path: str, **kw) -> Union[dict, list]:
        """
        Wrapped-entity-aware POST function.

        Creates a resource and returns the created entity if successful.

        :param path:
            The path/URL to which to send the POST request, which should be an
            index endpoint.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.post``
        :returns:
            The API response after JSON-decoding and unwrapping
        """
        return self.post(path, **kw)


    @resource_url
    @wrapped_entities
    def rput(self, resource: Union[str, dict], **kw) -> Optional[Union[dict, list]]:
        """
        Wrapped-entity-aware PUT function.

        Update an individual resource, returning the wrapped entity.

        :param resource:
            The path/URL to which to send the request, or a dict object
            representing an API resource that contains an item with key ``self``
            whose value is the URL of the resource.
        :param **kw:
            Custom keyword arguments to pass to ``requests.Session.put``
        :returns:
            The API response after JSON-decoding and unwrapping. In the case of at least
            one Teams endpoint (within REST API v2) and any other future API endpoint
            that responds with 204 No Content, the return value will be None.
        """
        return self.put(resource, **kw)

    @property
    def total_call_count(self) -> int:
        """The total number of API calls made by this instance."""
        return sum(self.api_call_counts.values())

    @property
    def total_call_time(self) -> float:
        """The total time spent making API calls."""
        return sum(self.api_time.values())



.. _user_guide:

==========
User Guide
==========

This is a topical guide to general API client usage. :ref:`module_reference`
has in-depth documentation on client classes and methods.



Installation
------------
This library is available on the Python Package Index as `pagerduty <https://pypi.org/project/pagerduty/>`_, e.g.: 

.. code-block:: bash

    pip install pagerduty

Command Line Interface
----------------------
This package also includes a basic CLI for PagerDuty Events API V2. For
example, to trigger an incident:

.. code-block:: bash

    pagerduty trigger -k $ROUTING_KEY --description "Network latency is high"

For more details, use the ``-h`` flag to display the script's helptext.

Authentication
--------------
The first step is to construct a client object. The first argument to the
constructor is the secret to use for accessing the API:

.. code-block:: python

    import pagerduty

    # REST API v2:
    client = pagerduty.RestApiV2Client(API_KEY)

    # REST API v2 with an OAuth2 access token (both are equivalent)
    client_oauth = pagerduty.RestApiV2Client(OAUTH_TOKEN, auth_type='oauth2')
    client_oauth = pagerduty.RestApiV2Client(OAUTH_TOKEN, auth_type='bearer')

    # Events API v2, including change events:
    events_client = pagerduty.EventsApiV2Client(ROUTING_KEY)

Session objects, being descendants of `requests.Session`_, can also be used as
context managers. For example:

.. code-block:: python

    with pagerduty.RestApiV2Client(API_KEY) as client:
        do_application(client)

Using Non-US Service Regions
****************************
If your PagerDuty account is in the EU or other service region outside the US, set the ``url`` attribute according to the
documented `API Access URLs
<https://support.pagerduty.com/docs/service-regions#api-access-urls>`_, i.e. for the EU:

.. code-block:: python

    # REST API
    client.url = 'https://api.eu.pagerduty.com'
    # Events API:
    events_client.url = 'https://events.eu.pagerduty.com'

The From header
***************
This request header can be set for all requests using the attribute
:attr:`pagerduty.RestApiV2Client.default_from` property, either directly or
through the ``default_from`` keyword argument when instantiating the client
object:

.. code-block:: python

    client = pagerduty.RestApiV2Client(API_KEY, default_from="admin@example.com")

If using an account-level API key, created by an administrator via the "API
Access Keys" page in the "Integrations" menu, a ``From`` header must be set in
requests to certain API endpoints, e.g. acknowledging or resolving incidents.
Its value must be the email address of a valid PagerDuty user. 

Otherwise, if using a user's API key (created under "API Access" in the "User
Settings" tab of the user's profile), the user will be derived from the key
itself and it is not necessary to set ``default_from`` or supply a ``From``
header.

If the source of the API key is unknown, the value of the client object's
property :attr:`pagerduty.RestApiV2Client.api_key_access` can be used. It will
be ``account`` if its API secret is an account-level API key, and it will be
``user`` for a user-level API key.

Performing an OAuth Exchange to Obtain an Access Token
******************************************************
The client class :class:`pagerduty.OAuthTokenClient` provides methods
implementing the OAuth exchange requests described in `Obtaining a User OAuth
Token via Code Grant
<https://developer.pagerduty.com/docs/user-oauth-token-via-code-grant>`_ and
`Obtaining an App OAuth Token
<https://developer.pagerduty.com/docs/app-oauth-token>`_.

.. code-block:: python

    token_client = pagerduty.OAuthTokenClient(client_secret, client_id)

To generate the URL that the user must visit to authorize the application:

.. code-block:: python

    # With a client object:
    authorize_url = token_client.authorize_url(scope, redirect_uri)

    # Without a client object:
    authorize_url = pagerduty.OAuthTokenClient.get_authorize_url(client_id, scope, redirect_uri)

The application must provide a redirect URI at which to receive the
authorization code parameter. Once the user visits, has authorized the
application and is redirected back to the application at the redirect URI, the
``code`` parameter appended to it will contain the authorization code. The code
can then be exchanged for an access token as following:

.. code-block:: python

    # auth_code contains the "code" parameter in the redirect URL of the application:
    auth_response = token_client.get_new_token_from_code(auth_code, scope, redirect_uri)
    access_token = auth_response['access_token']
    refresh_token = auth_response['refresh_token']

Performing OAuth Token Refresh Automatically
********************************************
As of version 3.0.0, the OAuth response dictionary returned by token-getting
methods of :class:`pagerduty.OAuthTokenClient` will include a property
``expiration_date`` containing a string that is an ISO8601-formatted date/time
indicating when the included token will expire. Assuming that your application
securely stores this string value in addition to ``access_token`` and
``refresh_token``, and has the means to retrieve these values, they can be used
to call :attr:`pagerduty.OAuthTokenClient.refresh_client`, which instantiates a
new :class:`pagerduty.RestApiV2Client` and automatically refreshes the access
token as necessary.

.. code-block:: python

    # Assume the calling application implements methods securely_get_values and
    # securely_store_values to recall and store secrets used for API access:
    access_token, refresh_token, expiration_date = securely_get_values()
    rest_client, auth_response = token_client.refresh_client(
        access_token,
        refresh_token,
        expiration_date
    )
    # If auth_response == None, the token was not refreshed and does not need
    # to be updated; otherwise it will be similar to the value returned by
    # other token-getting methods:
    if type(auth_response) is dict:
        securely_store_values(
            access_token = auth_response['access_token'],
            refresh_token = auth_response['refresh_token'],
            expiration_date = auth_response['expiration_date']
        )


Note, the current default behavior of :class:`OAuthTokenClient` is to refresh
the token if it is going to expire less than 24 hours in the future. This
"buffer time" (expressed as a positive integer number of seconds in the future)
can be controlled by setting the property
:attr:`pagerduty.OAuthTokenClient.early_refresh_buffer`.

Basic Usage Examples
--------------------

REST API v2
***********

**Making a request and decoding the response:** obtaining a resource's contents
and having them represented as a dictionary object using three different methods:

.. code-block:: python

    # Using get:
    response = client.get('/users/PABC123')
    user = None
    if response.ok:
        user = response.json()['user']

    # Using jget (return the full body after decoding):
    user = client.jget('/users/PABC123')['user']

    # Using rget (return the response entity after unwrapping):
    user = client.rget('/users/PABC123')

    # >>> user
    # {"type": "user", "email": "user@example.com", ... }

**Using pagination:** ``iter_all``, ``iter_cursor``, ``list_all`` and
``dict_all`` can be used to obtain results from a resource collection:

.. code-block:: python

    # Print each user's email address and name:
    for user in client.iter_all('users'):
        print(user['id'], user['email'], user['name'])

**Pagination with query parameters:** set the ``params`` keyword argument, which is
converted to URL query parameters by Requests_:

.. code-block:: python

    # Get a list of all services with "SN" in their name:
    services = client.list_all('services', params={'query': 'SN'})

    # >>> services
    # [{'type':'service', ...}, ...]

**Searching resource collections:** use ``find`` to look up a resource (a user,
in this example) exactly matching a string using the ``query`` parameter on an
index endpoint:

.. code-block:: python

    # Find the user with email address "jane@example35.com"
    user = client.find('users', 'jane@example35.com', attribute='email')

    # >>> user
    # {'type': 'user', 'email': 'jane@example35.com', ...}

**Getting a count of records:** use ``get_total`` on any endpoint
that supports classic pagination:

.. code-block:: python

    # Get the total number of users in the whole account:
    total_users = client.get_total('users')

    # Get the total number of users on a given team:
    total_users_on_team_x = client.get_total(
        'users',
        params = {'team_ids[]': ['PGHI789']}
    )

**Updating a resource:** use the ``json`` keyword argument to set the body of the request:

.. code-block:: python

    # >>> user
    # {'self':'https://api.pagerduty.com/users/PABC123', 'type': 'user', ...}

    # (1) using put directly:
    updated_user = None
    response = client.put(user['self'], json={
        'user': {
            'type':'user',
            'name': 'Jane Doe'
        }
    })
    if response.ok:
        updated_user = response.json()['user']

    # (2) using rput:
    #   - The URL argument may also be a resource / resource reference dict
    #   - The json argument doesn't have to include the "user" wrapper dict
    #   - If an HTTP error is encountered, it will raise an exception
    updated_user = client.rput(user, json={
        'type':'user',
        'name': 'Jane Doe'
    })

**Idempotent create/update:** create a user if one doesn't already exist based
on the dictionary object ``user_data``, using the "email" key/property as the
uniquely identifying attribute, and update it if it exists and differs from
``user_data``:

.. code-block:: python

    user_data = {'email': 'user123@example.com', 'name': 'User McUserson'}
    updated_user = client.persist('users', 'email', user_data, update=True)

**Using multi-valued set filters:** set the value in the ``params`` dictionary
at the appropriate key to a list. Square brackets will then be automatically
appended to the names of list-type-value parameters as necessary. For example:

.. code-block:: python

    # Query all open incidents assigned to a user
    incidents = client.list_all(
        'incidents',
        params={
          # Both of the following parameter names are valid:
          'user_ids[]': ['PHIJ789'],
          'statuses': ['triggered', 'acknowledged'] # "[]" will be automatically appended
        }
    )
    # API calls will look like the following:
    # GET /incidents?user_ids%5B%5D=PHIJ789&statuses%5B%5D=triggered&statuses%5B%5D=acknowledged&offset=0&limit=100

**Get a list of all incident notes submitted by a team within a time range:**

.. code-block:: python

    notes = list(client.iter_incident_notes(params={
        'team_ids':['PN1T34M'],
        'since': '2025-01-01',
        'until': '2025-07-01'
    }))

    # >>> notes
    # [{'type': 'annotate_log_entry', 'summary': 'Resolved by reboot' ... }, ... ]

**Performing multi-update:** for endpoints that support it only, i.e. ``PUT /incidents``:

.. code-block:: python

    # Acknowledge all triggered incidents assigned to a user:
    incidents = client.list_all(
        'incidents',
        params={'user_ids':['PHIJ789'],'statuses':['triggered']}
    )
    for i in incidents:
        i['status'] = 'acknowledged'
    updated_incidents = client.rput('incidents', json=incidents)

Events API v2
*************
**Trigger and resolve an alert,** getting its deduplication key from the API, using :class:`pagerduty.EventsApiV2Client`:

.. code-block:: python

    dedup_key = events_client.trigger("Server is on fire", 'dusty.old.server.net') 
    # ...
    events_client.resolve(dedup_key)

**Trigger an alert and acknowledge it** using a custom deduplication key:

.. code-block:: python

    events_client.trigger("Server is on fire", 'dusty.old.server.net',
        dedup_key='abc123')
    # ...
    events_client.acknowledge('abc123')

**Submit a change event** using a :class:`pagerduty.EventsApiV2Client` instance:

.. code-block:: python

    events_client.submit("new build finished at latest HEAD",
        source="automation")

Generic Client Features
-----------------------
Generally, all of the features of `requests.Session`_ are available to the user
as they would be if using the Requests Python library directly, since
:class:`pagerduty.ApiClient` and its subclasses for the REST/Events APIs are
descendants of it. 

The ``get``, ``post``, ``put`` and ``delete`` methods of REST/Events API
client classes are similar to the analogous functions in `requests.Session`_.
The arguments they accept are the same and they all return `requests.Response`_
objects.

Any keyword arguments passed to the ``j*`` or ``r*`` methods will be passed
through to the analogous method in Requests_, though in some cases the
arguments (i.e. ``json``) are first modified.

For documentation on any generic HTTP client features that are available, refer
to the Requests_ documentation.

URLs
----
The first argument to most of the client methods is the URL. However, there is
no need to specify a complete API URL. Any path relative to the root of the
API, whether or not it includes a leading slash, is automatically normalized to
a complete API URL.  For instance, one can specify ``users/PABC123`` or
``/users/PABC123`` instead of ``https://api.pagerduty.com/users/PABC123``.

One can also pass the full URL of an API endpoint and it will still work, i.e.
the ``self`` property of any object can be used, and there is no need to strip
out the API base URL.

The ``r*`` and ``j*`` methods, i.e.  :attr:`pagerduty.RestApiV2Client.rget`,
can also accept a dictionary object representing an API resource or a resource
reference (see: `resource references`_) in place of a URL, in which case the
value at its ``self`` key will be used as the request URL.

Query Parameters
----------------
As with `Requests`_, there is no need to compose the query string (everything
that will follow ``?`` in the URL). Simply set the ``params`` keyword argument
to a dictionary, and each of the key/value pairs will be serialized to the
query string in the final URL of the request:

.. code-block:: python

    first_dan = client.rget('users', params={
        'query': 'Dan',
        'limit': 1,
        'offset': 0,
    })
    # GET https://api.pagerduty.com/users?query=Dan&limit=1&offset=0

To specify a multi-value parameter, i.e. ``include[]``, set the argument to a
list. If a list is given, and the key name does not end with ``[]`` (which is
required for all such multi-valued parameters in REST API v2), then ``[]`` will
be automatically appended to the parameter name. For example:

.. code-block:: python

    # If there are 82 services with name matching "foo" this will return all of
    # them as a list:
    foo_services = client.list_all('services', params={
        'query': 'foo',
        'include': ['escalation_policies', 'teams'],
        'limit': 50,
    })
    # GET https://api.pagerduty.com/services?query=foo&include%5B%5D=escalation_policies&include%5B%5D=teams&limit=50&offset=0
    # GET https://api.pagerduty.com/services?query=foo&include%5B%5D=escalation_policies&include%5B%5D=teams&limit=50&offset=50
    # >>> foo_services
    # [{"type": "service" ...}, ... ]


Requests and Responses
----------------------
To set the request body in a post or put request, pass as the ``json`` keyword
argument an object that will be JSON-encoded as the body.

To obtain the response from the API, if using plain ``get``, ``post``, ``put``
or ``delete``, use the returned `requests.Response`_ object. That object's
``json()`` method will return the result of JSON-decoding the response body (it
will typically of type ``dict``). Other metadata such as headers can also be
obtained:

.. code-block:: python

    response = client.get('incidents')
    # The UUID of the API request, which can be supplied to PagerDuty Customer
    # Support in the event of server errors (status 5xx):
    print(response.headers['x-request-id'])

If using the ``j*`` methods, i.e. :attr:`pagerduty.RestApiV2Client.jget`, the return value
will be the full body of the response from the API after JSON-decoding, and
the ``json`` keyword argument is not modified.

When using the ``r*`` methods, the ``json`` keyword argument is modified before
sending to Requests_, if necessary, to encapsulate the body inside an entity
wrapper.  The response is the decoded body after unwrapping, if the API
endpoint returns wrapped entities. For more details, refer to :ref:`wrapping`.

Data types
**********
Main article: `Types <https://developer.pagerduty.com/docs/types>`_

Note these analogues in structure between the JSON schema and the object
in Python:

* If the data type documented in the schema is
  "object", then the corresponding type of the Python object will be ``dict``.
* If the data type documented in the schema is
  "array", then the corresponding type of the Python object will be ``list``.
* Generally speaking, the data type in the decoded object is according to the
  design of the `json <https://docs.python.org/3/library/json.html>`_ Python library.

For example, consider the example structure of an escalation policy as given in
the API reference page for ``GET /escalation_policies/{id}`` ("Get an
escalation policy"). To access the name of the second target in level 1,
assuming the variable ``ep`` represents the unwrapped escalation policy object:

.. code-block:: python

    ep['escalation_rules'][0]['targets'][1]['summary']
    # "Daily Engineering Rotation"

To add a new level, one would need to create a new escalation rule as a
dictionary object and then append it to the ``escalation rules`` property.
Using the example given in the API reference page:

.. code-block:: python

    new_rule = {
        "escalation_delay_in_minutes": 30,
        "targets": [
            {
                "id": "PAM4FGS",
                "type": "user_reference"
            },
            {
                "id": "PI7DH85",
                "type": "schedule_reference"
            }
        ]
    }
    ep['escalation_rules'].append(new_rule)
    # Save changes:
    ep = client.rput(ep, json=ep)

Resource Schemas
****************
Main article: `Resource Schemas <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU5-resource-schemas>`_

The details of any given resource's schema can be found in the request and
response examples from the `PagerDuty API Reference`_ pages for the resource's
respective API, as well as the page documenting the resource type itself.

.. _wrapping:

Entity Wrapping
---------------
See also: `Wrapped Entities <https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYx-wrapped-entities>`_.
Most of PagerDuty's REST API v2 endpoints respond with their content wrapped
inside of another object with a single key at the root level of the
(JSON-encoded) response body, and/or require the request body be wrapped in
another object that contains a single key. Endpoints with such request/response
schemas usually (with few exceptions) support pagination.

Identifying Wrapped-entity Endpoints
************************************
*If the endpoint's response schema or expected request schema contains only one
property that contains all of the content of the API resource, the endpoint is
said to wrap entities.* In resource collection endpoints that support
pagination, the response schema contains additional pagination-related
properties such as ``more`` (for classic pagination) or ``next_cursor`` (for
cursor-based pagination) and no other content-bearing properties.

Wrapped-entity-aware Functions
******************************
The following methods will automatically extract and return the wrapped content
of API responses, and wrap request entities for the user as appropriate:

* :attr:`pagerduty.RestApiV2Client.dict_all`: Create a dictionary of all results from a resource collection
* :attr:`pagerduty.RestApiV2Client.find`: Find and return a specific result of a resource collection that matches a query
* :attr:`pagerduty.RestApiV2Client.iter_all`: Iterate through all results of a resource collection
* :attr:`pagerduty.RestApiV2Client.iter_cursor`: Iterate through all results of a resource collection using cursor-based pagination
* :attr:`pagerduty.RestApiV2Client.list_all`: Create a list of all results from a resource collection
* :attr:`pagerduty.RestApiV2Client.persist`: Create a resource entity with specified attributes if one that matches them does not already exist
* :attr:`pagerduty.RestApiV2Client.rget`: Get the wrapped entity or resource collection at a given endpoint
* :attr:`pagerduty.RestApiV2Client.rpost`: Send a POST request, wrapping the request entity / unwrapping the response entity
* :attr:`pagerduty.RestApiV2Client.rput`: Send a PUT request, wrapping the request entity / unwrapping the response entity

Special Cases
*************
There are some API endpoints that do not follow API schema conventions for
entity wrapping. Some do not wrap entities at all. On all endpoints that do not
wrap entities, the results for a given ``r*`` method would be the same if using
the equivalent ``j*`` method, and the details of request and response schemas
are are left to the end user to extract and use as desired. Moreover, on all
endpoints that completely lack entity wrapping, pagination is not supported,
i.e. :attr:`pagerduty.RestApiV2Client.iter_all` will raise
:attr:`pagerduty.UrlError` if used with them.

Examples
********
The endpoint "Create Business Service Subscribers", or ``POST
/business_services/{id}/subscribers``, wraps the response differently from the
request. The end user can still pass the content to be wrapped via the ``json``
argument without the ``subscribers`` wrapper, while the return value is the
list representing the content inside of the ``subscriptions`` wrapper in the
response, and there is no need to hard-code any particular endpoint's wrapper
name into the usage of the client.

Some endpoints are unusual in that the request must be wrapped but the response
is not wrapped or vice versa, i.e. creating Schedule overrides (``POST
/schedules/{id}/overrides``) or to create a status update on an incient (``POST
/incidents/{id}/status_updates``).  In all such cases, the user still does not
need to account for this, as the content will be returned and the request
entity is wrapped as appropriate.

What that looks like, for the "Create one or more overrides" endpoint:

.. code-block:: python

    created_overrides = client.rpost('/schedules/PGHI789/overrides', json=[
        {
            "start": "2023-07-01T00:00:00-04:00",
            "end": "2023-07-02T00:00:00-04:00",
            "user": {
                "id": "PEYSGVA",
                "type": "user_reference"
            },
            "time_zone": "UTC"
        },
        {
            "start": "2023-07-03T00:00:00-04:00",
            "end": "2023-07-01T00:00:00-04:00",
            "user": {
                "id": "PEYSGVF",
                "type": "user_reference"
            },
            "time_zone": "UTC"
        }
    ])
    # >>> created_overrides
    # [
    #     {'status': 201, 'override': {...}},
    #     {'status': 400, 'errors': ['Override must end after its start'], 'override': {...}}
    # ]


Pagination
----------
Main article: `Pagination <https://developer.pagerduty.com/docs/pagination>`_

Only classic and cursor-based pagination are currently supported. Pagination
functions require that the API endpoint being requested have entity wrapping
enabled, and respond with either a ``more`` or ``cursor`` property indicating
how and if to fetch the next page of results.

The method :attr:`pagerduty.RestApiV2Client.iter_all` returns an iterator that
yields results from an endpoint that features pagination. The methods
:attr:`pagerduty.RestApiV2Client.list_all` and
:attr:`pagerduty.RestApiV2Client.dict_all` will request all pages of the
collection and return the results as a list or dictionary, respectively.

Examples:

.. code-block:: python

    # Example: Find all users with "Dav" in their name/email (i.e. Dave/David)
    # in the PagerDuty account:
    for dave in client.iter_all('users', params={'query':"Dav"}):
        print("%s <%s>"%(dave['name'], dave['email']))

    # Example: Get a dictionary of all users, keyed by email, and use it to
    # find the ID of the user whose email is ``bob@example.com``
    users = client.dict_all('users', by='email')
    print(users['bob@example.com']['id'])

    # Same as above, but using ``find``:
    bob = client.find('users', 'bob@example.com', attribute='email')
    print(bob['id'])

By default, classic, a.k.a. numeric pagination, will be used. If the endpoint
supports cursor-based pagination, it will call out to
:attr:`pagerduty.RestApiV2Client.iter_cursor` to iterate through results
instead.

Retrieving Large Historical Datasets
************************************
`Classic pagination
<https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTU4-pagination#classic-pagination>`_
in REST API v2 has a hard limit of 10,000 records (see
:attr:`pagerduty.rest_api_v2_client.ITERATION_LIMIT`). In other words, if the sum of the ``limit``
and ``offset`` parameters is larger than this value, the API will respond with
HTTP 400 Invalid Request. To get around this issue and retrieve larger data
sets, one must either filter the results such that the total is less than this
hard limit, or break the data set down into smaller time windows using the
``since`` and ``until`` parameters, for APIs that support them.

In version 3.0.0, the method :attr:`pagerduty.RestApiV2Client.iter_history` was
added to facilitate retrieiving large datasets of historical records, i.e.
``/log_entries``. To use it, first construct timezone-aware
``datetime.datetime`` objects (see: `datetime
<https://docs.python.org/3/library/datetime.html>`_) that correspond to the
absolute beginning and end of the time interval from which to retrieive
records. The method will then automatically figure out how to divide the time
interval so that it can retrieve all records from sub-intervals without running
into the hard pagination limit.

For example, to obtain all log entries (incident/alert timeline events) year-to-date:

.. code-block:: python

    from datetime import datetime, timezone
    until = datetime.now(timezone.utc)
    since = datetime(until.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # Assume "client" is an instance of RestApiV2Client and "process_ile" is a
    # storage and/or data reduction/aggregation method:
    for log_entry in client.iter_history('/log_entries', since,  until):
        process_ile(log_entry)

It is recommended to perform action on each item once it has been yielded, i.e.
to persist it in a data warehouse, rather than constructing big a list of
results and then operating on the list. That is because, if anything goes
wrong while fetching the dataset, i.e. an exception is raised or the program
runs out of memory, the partial data it retrieved will be lost to garbage
collection.

Non-Standard Pagination Styles
******************************
For all endpoints that implement one of the standard pagination methods
(classic or cursor-based), :attr:`pagerduty.RestApiV2Client.iter_all` will
work. However, as of this writing, there are two API endpoints known to have
their own special pagination style. Dedicated abstractions for them include:

* `Get raw data - multiple incidents (analytics) <https://developer.pagerduty.com/api-reference/c2d493e995071-get-raw-data-multiple-incidents>`_ / ``POST /analytics/raw/incidents``: :attr:`pagerduty.RestApiV2Client.iter_analytics_raw_incidents`
* `List alert grouping settings <https://developer.pagerduty.com/api-reference/b9fe211cc2748-list-alert-grouping-settings>`_ / ``GET /alert_grouping_settings``: :attr:`pagerduty.RestApiV2Client.iter_alert_grouping_settings`

These methods must be used on said endpoints; using the standard pagination
methods such as ``iter_all``, ``iter_cursor`` or ``iter_history`` on them will not work
properly.

Performance and Completeness of Results
***************************************
Because HTTP requests are made synchronously and not in multiple threads,
requesting all pages of data will happen one page at a time and the functions
``list_all`` and ``dict_all`` will not return until after the final HTTP
response. Simply put, the functions will take longer to return if the total
number of results is higher.

Moreover, if these methods are used to fetch a very large volume of data, and
an error is encountered when this happens, the partial data set will be
discarded when the exception is raised. To make use of partial results, perform
actions on each result using an ``iter_*`` method and catch/handle exceptions
as desired.

Updating, creating or deleting while paginating
***********************************************
If performing page-wise write operations, i.e. making persistent changes to the
PagerDuty application state immediately after fetching each page of results, an
erroneous condition can result if there is any change to the resources in the
result set that would affect their presence or position in the set. For
example, creating objects, deleting them, or changing the attribute being used
for sorting or filtering.

This is because the contents are updated in real time, and pagination contents
are recalculated based on the state of the PagerDuty application at the time of
each request for a page of results. Therefore, records may be skipped or
repeated in results if the state changes, because the content of any given page
will change accordingly. Note also that changes made from other processes,
including manual edits through the PagerDuty web application, can have the same
effect.

To elaborate: let's say that each resource object in the full list is a page in
a notebook. Classic pagination with ``limit=100`` is essentially "go through
100 pages, then repeat starting with the 101st page, then with the 201st, etc."
Deleting records in-between these 100-at-a-time pagination requests would be
like tearing out pages after reading them. At the time of the second page
request, what was originally the 101st page before starting will shift to
become the first page after tearing out the first hundred pages. Thus, when
going to the 101st page after finishing tearing out the first hundred pages,
the second hundred pages will be skipped over, and similarly for pages 401-500,
601-700 and so on. If attaching pages, the opposite happens: some results will be
returned more than once, because they get bumped to the next group of 100 pages.

Multi-updating
--------------
Multi-update actions can be performed using ``rput`` with some endpoints. For
instance, to resolve two incidents with IDs ``PABC123`` and ``PDEF456``:

.. code-block:: python

    client.rput(
        "incidents",
        json=[
            {'id':'PABC123','type':'incident_reference', 'status':'resolved'},
            {'id':'PDEF456','type':'incident_reference', 'status':'resolved'},
        ],
    )

In this way, a single API request can more efficiently perform multiple update
actions.

It is important to note, however, that updating incidents requires using a
user-scoped access token or setting the ``From`` header to the login email
address of a valid PagerDuty user. To set this, pass it through using the
``headers`` keyword argument, or set the
:attr:`pagerduty.RestApiV2Client.default_from` property, or pass the email
address as the ``default_from`` keyword argument when constructing the client
initially.

Error Handling
--------------
The :class:`pagerduty.UrlError` is raised prior to making API calls, and it indicates
unsupported URLs and/or malformed input.

The base exception class for all errors encountered when making requests is
:class:`pagerduty.Error`. This includes network / transport issues where there
is no response from the API, in which case the exception will inherit from the
exception raised by the underlying HTTP library.

All errors that involve a response from the API are instances of
:class:`pagerduty.HttpError` and will have a ``response`` property containing
the `requests.Response`_ object. Its subclass
:class:`pagerduty.HttpServerError` is used for special cases when the API is
responding in an unexpected way.

One can thus define specialized error handling logic in which the REST API
response data (i.e.  headers, code and body) are available in the catching
scope. For example, the following code prints "User not found" in the event of a 404,
prints out the user's email if the user exists and raises the underlying
exception if it's any other HTTP error code:

.. code-block:: python

    try:
        user = client.rget("/users/PJKL678")
        print(user['email'])

    except pagerduty.HttpError as e:
        if e.response.status_code == 404:
            print("User not found")
        else:
            raise e

Logging
-------
When a client object is instantiated, a
`Logger object <https://docs.python.org/3/library/logging.html#logger-objects>`_
is created as follows:

* Its level is unconfigured (``logging.NOTSET``) which causes it to defer to the 
  level of the parent logger. The parent is the root logger unless specified
  otherwise (see `Logging Levels
  <https://docs.python.org/3/library/logging.html#logging-levels>`_).
* The logger is initially not configured with any handlers. Configuring
  handlers is left to the discretion of the user (see `logging.handlers
  <https://docs.python.org/3/library/logging.handlers.html>`_)
* The logger can be accessed and set through the property
  :attr:`pagerduty.ApiClient.log`.

The attribute :attr:`pagerduty.ApiClient.print_debug` enables sending
debug-level log messages from the client to command line output. It is used as
follows:

.. code-block:: python

    # Method 1: keyword argument, when constructing a new client:
    client = pagerduty.RestApiV2Client(api_key, debug=True)

    # Method 2: on an existing client, by setting the property:
    client.print_debug = True

    # to disable:
    client.print_debug = False

What this does is assign a `logging.StreamHandler
<https://docs.python.org/3/library/logging.handlers.html#streamhandler>`_
directly to the client's logger and set the log level to ``logging.DEBUG``.
All log messages are then sent directly to ``sys.stderr``. The default value
for all clients is ``False``, and it is recommended to keep it that way in
production systems.

Using a Proxy Server
--------------------
To configure the client to use a host as a proxy for HTTPS traffic, update the
``proxies`` attribute:

.. code-block:: python

    # Host 10.42.187.3 port 4012 protocol https:
    client.proxies.update({'https': '10.42.187.3:4012'})

HTTP Retry Configuration
------------------------
Session objects support retrying API requests if they receive a non-success
response or if they encounter a network error.

This behavior is configurable through the following properties:

* :attr:`pagerduty.ApiClient.retry`: a dictionary that allows defining per-HTTP-status retry limits
* :attr:`pagerduty.ApiClient.max_http_attempts`: The maximum total number of unsuccessful requests to make in the retry loop of :attr:`pagerduty.ApiClient.request` before returning
* :attr:`pagerduty.ApiClient.max_network_attempts`: The maximum number of retries that will be attempted in the case of network or non-HTTP error
* :attr:`pagerduty.ApiClient.sleep_timer`: The initial cooldown factor
* :attr:`pagerduty.ApiClient.sleep_timer_base`: Factor by which the cooldown time is increased after each unsuccessful attempt
* :attr:`pagerduty.ApiClient.stagger_cooldown`: Randomizing factor for increasing successive cooldown wait times

Default Behavior
****************
By default, after receiving a status 429 response, clients will retry an
unlimited number of times, increasing the wait time before retry each
successive time.  When encountering status ``401 Unauthorized``, the client
will immediately raise :attr:`pagerduty.HttpError`; this is a non-transient error
caused by an invalid credential.

For all other success or error statuses, the underlying request method in the
client will return the `requests.Response`_ object.

Exponential Cooldown
********************
After each unsuccessful attempt, the client will sleep for a short period that
increases exponentially with each retry.

Let:

* a = :attr:`pagerduty.ApiClient.sleep_timer_base` (base of the exponent, default value ``2``)
* t\ :sub:`0` = :attr:`pagerduty.ApiClient.sleep_timer` (initial sleep timer, default value ``1.5``)
* t\ :sub:`n` = Sleep time after n attempts
* ρ = :attr:`pagerduty.ApiClient.stagger_cooldown`
* r\ :sub:`n` = a randomly-generated real number between 0 and 1, distinct for each n-th request

Assuming ρ = 0 (the default value):

t\ :sub:`n` = t\ :sub:`0` a\ :sup:`n`

If ρ is nonzero:

t\ :sub:`n` = a (1 + ρ r\ :sub:`n`) t\ :sub:`n-1`

Configuring Retry Behavior
**************************
The dictionary property :attr:`pagerduty.ApiClient.retry` allows customization of
HTTP retry limits on a per-HTTP-status basis. This includes the ability to
override the above defaults for 401 and 429, although that is not recommended.

Each key in the dictionary represents a HTTP status, and its associated value
the number of times that the client will retry the request if it receives
that status. **Success statuses (2xx) will be ignored.**

If a different error status is encountered on a retry, it won't count towards
the limit of the first status, but will be counted separately. However, the
total overall number of attempts that will be made to get a success status is
limited by :attr:`pagerduty.ApiClient.max_http_attempts`. This will always
supersede the maximum number of retries for any status defined in
:attr:`pagerduty.ApiClient.retry` if it is lower.

Low-level HTTP request functions in client classes, i.e. ``get``, will return
`requests.Response`_ objects when they run out of retries. Higher-level
functions that require a success status response, i.e.
:attr:`pagerduty.RestApiV2Client.list_all` and
:attr:`pagerduty.EventsApiV2Client.trigger`, will raise instances of
:class:`pagerduty.HttpError`, but only after the configured retry limits are
reached in the underlying HTTP request methods.

**Example:**

.. code-block:: python

    # This will take about 30 seconds plus API request time, carrying out four
    # attempts with 2, 4, 8 and 16 second pauses between them, before finally
    # returning the status 404 response object for the user that doesn't exist:
    client.max_http_attempts = 4 # lower value takes effect
    client.retry[404] = 5 # this won't take effect
    client.sleep_timer = 1
    client.sleep_timer_base = 2
    response = client.get('/users/PNOEXST')

    # Same as the above, but with the per-status limit taking precedence, so
    # the total wait time is 62 seconds:
    client.max_http_attempts = 6
    response = client.get('/users/PNOEXST')

.. References:
.. -----------

.. _`Requests`: https://docs.python-requests.org/en/master/
.. _`Errors`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTYz-errors
.. _`Events API v2`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview
.. _`PagerDuty API Reference`: https://developer.pagerduty.com/api-reference/
.. _`REST API v2`: https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTUw-rest-api-v2-overview
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions
.. _`resource references`: https://developer.pagerduty.com/docs/resource-references

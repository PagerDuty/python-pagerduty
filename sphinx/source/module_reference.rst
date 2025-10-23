.. _module_reference:

================
Module Reference
================

This page covers the documentation of individual methods and classes provided
by the package. For general usage and examples, refer to the :ref:`user_guide`.

API Client Classes
------------------
For convenience and backwards compatibility, the API client classes supplied by
this library are imported into the root namespace of the module. For example:

.. code-block:: python

    # Instead of this:
    from pagerduty.rest_api_v2_client import RestApiV2Client

    # One can write the import as:
    from pagerduty import RestApiV2Client

.. autoclass:: pagerduty.ApiClient
    :members:

.. autoclass:: pagerduty.OAuthTokenClient
    :members:

.. autoclass:: pagerduty.RestApiV2BaseClient
    :members:

.. autoclass:: pagerduty.RestApiV2Client
    :members:

.. autoclass:: pagerduty.EventsApiV2Client
    :members:

.. autoclass:: pagerduty.JiraCloudIntegrationApiClient
    :members:

.. autoclass:: pagerduty.JiraServerIntegrationApiClient
    :members:

.. autoclass:: pagerduty.MsTeamsIntegrationApiClient
    :members:

.. autoclass:: pagerduty.SlackIntegrationApiClient
    :members:

.. autoclass:: pagerduty.SlackIntegrationConnectionsApiClient
    :members:

.. autoclass:: pagerduty.McpApiClient
    :members:

.. autoclass:: pagerduty.ScimApiClient
    :members:

AuthMethod Classes
------------------
Constructing an API client requires setting its ``auth_method`` property to an
``AuthMethod`` object. This object stores API credentials and specifies how the
credentials are sent to the API. In most implementations of
:class:`ApiClient`, for backwards compatibility, this is done without user
intervention i.e. by accepting a string argument in the constructor that
represents the API credential and then constructing an object of the
appropriate ``AuthMethod`` subclass for its corresponding API.

In most use cases, to use a new API key in an existing process, it is
appropriate to simply instantiate a new client object with the new key.

For use cases that require reusing existing client objects, it is necessary to
set the :attr:`pagerduty.ApiClient.auth_method` property to a new
``AuthMethod`` object with the new credential. Note that each API client must
be supplied with an instance of an appropriate ``AuthMethod`` subclass, or it
may not authenticate properly with the API in question. Refer to its
``__init__`` definition to discover this class, or find the corresponding
``AuthMethod`` class for it below:

.. autoclass:: pagerduty.auth_method.AuthMethod
    :members:

.. autoclass:: pagerduty.auth_method.HeaderAuthMethod

.. autoclass:: pagerduty.auth_method.BodyParameterAuthMethod

.. autoclass:: pagerduty.rest_api_v2_base_client.TokenAuthMethod

.. autoclass:: pagerduty.rest_api_v2_base_client.OAuthTokenAuthMethod

.. autoclass:: pagerduty.auth_method.PassThruHeaderAuthMethod

.. autoclass:: pagerduty.events_api_v2_client.RoutingKeyAuthMethod

.. autoclass:: pagerduty.oauth_token_client.ClientCredentialsAuthMethod


Errors
------
As with client classes, all errors are imported to the root module
namespace, so that one can import them directly from ``pagerduty``.

.. autoclass:: pagerduty.Error
    :members:
.. autoclass:: pagerduty.HttpError
    :members:
.. autoclass:: pagerduty.ServerHttpError
    :members:
.. autoclass:: pagerduty.UrlError
    :members:

Common Features
---------------
Miscellaneous methods and constants used in the client that are used widely
and/or don't fit neatly into any other category are defined in
``pagerduty.common``.

A few of these features are imported to the root namespace for backwards
compatibility, but new features will not, going forward.

.. automodule:: pagerduty.common
    :members:

REST API v2 Helpers
-------------------
REST API v2 and the integration APIs have some common features, such as classic
pagination, which are implemented in ``rest_api_v2_base_client`` so as to be
able to repurpose them in APIs that follow similar conventions.

.. automodule:: pagerduty.rest_api_v2_base_client
    :members:
    :exclude-members: RestApiV2BaseClient

.. References:
.. -----------

.. _`HTTPX`: https://www.python-httpx.org/
.. _httpx.Response: https://www.python-httpx.org/api/#response
.. _httpx.Client: https://www.python-httpx.org/api/#client

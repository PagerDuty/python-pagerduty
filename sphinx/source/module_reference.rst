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

.. _`Requests`: https://docs.python-requests.org/en/master/
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions

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

.. autoclass:: pagerduty.RestApiV2LikeClient
    :members:

.. autoclass:: pagerduty.RestApiV2Client
    :members:

.. autoclass:: pagerduty.EventsApiV2Client
    :members:

.. autoclass:: pagerduty.SlackIntegrationApiClient
    :members:

.. autoclass:: pagerduty.SlackIntegrationConnectionsApiClient
    :members:

Errors
------
.. automodule:: pagerduty.errors
    :members:

Base API Client Helpers
-----------------------
.. automodule:: pagerduty.api_client
    :members:
    :exclude-members: ApiClient

Common Helper Methods
--------------------
.. automodule:: pagerduty.common
    :members:

REST API v2 Helpers
------------------

Common Features
***************
REST API v2 and the integration APIs (to some extent) have some common
features, such as classic pagination, which are implemented in
``rest_api_v2_like_client`` so as to be able to repurpose them in APIs that
follow similar conventions.

.. automodule:: pagerduty.rest_api_v2_like_client
    :members:
    :exclude-members: RestApiV2LikeClient

Features Exclusive to REST API v2
*********************************

.. automodule:: pagerduty.rest_api_v2_client
    :members:
    :exclude-members: RestApiV2Client

.. References:
.. -----------

.. _`Requests`: https://docs.python-requests.org/en/master/
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions

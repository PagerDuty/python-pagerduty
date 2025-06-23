.. _module_reference:

================
Module Reference
================

This page covers the documentation of individual methods and classes provided
by the module. For general usage and examples, refer to the :ref:`user_guide`.

API Client Classes
------------------
.. autoclass:: pagerduty.ApiClient
    :members:

.. autoclass:: pagerduty.OAuthTokenClient
    :members:

.. autoclass:: pagerduty.RestApiV2Client
    :members:

.. autoclass:: pagerduty.EventsApiV2Client
    :members:

Errors
------
.. autoclass:: pagerduty.Error
    :members:
.. autoclass:: pagerduty.HttpError
    :members:
.. autoclass:: pagerduty.ServerHttpError
    :members:
.. autoclass:: pagerduty.UrlError

Client Defaults
---------------
These are properties of the module that configure default behavior for the API
client. There should be no need for the end user to modify them.

.. automodule:: pagerduty.rest_api_v2_client
    :members: ITERATION_LIMIT, ENTITY_WRAPPER_CONFIG, CANONICAL_PATHS, CURSOR_BASED_PAGINATION_PATHS
.. automodule:: pagerduty.common
    :members: TEXT_LEN_LIMIT
.. automodule:: pagerduty.api_client
    :members: TIMEOUT

Functions
---------
These are generic functions used by the API session classes and are not on
their own typically needed, but which are documented for the benefit of anyone
who may find use in them.

URL Handling
************
URL related functions.

.. automodule:: pagerduty
    :members: canonical_path, endpoint_matches, is_path_param, normalize_url

Entity Wrapping
***************
Functions that implement entity wrapping logic.

.. automodule:: pagerduty
    :members: entity_wrappers, infer_entity_wrapper, unwrap

Function Decorators
*******************
Intended for use with functions based on the HTTP verb functions of subclasses
of `requests.Session`_, i.e. that would otherwise return a `requests.Response`_
object.

.. automodule:: pagerduty
    :members: auto_json, requires_success, resource_url, wrapped_entities

Helpers
*******
Miscellaneous functions

.. automodule:: pagerduty
    :members: deprecated_kwarg, http_error_message, last_4, plural_name, successful_response, truncate_text, try_decoding



.. References:
.. -----------

.. _`Requests`: https://docs.python-requests.org/en/master/
.. _requests.Response: https://docs.python-requests.org/en/master/api/#requests.Response
.. _requests.Session: https://docs.python-requests.org/en/master/api/#request-sessions

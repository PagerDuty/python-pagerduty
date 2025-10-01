**2025-10-01: 5.1.0: Maintenance update with entity wrapping support for new API endpoints**

* Entityh wrapping support added for new endpoints of APIs:
   * Incident types API
   * Webhooks API
   * Event Orchestrations cache variables
   * Per-service custom fields
   * OAuth clients (webhook subscriptions)
* Entity wrapping support not yet removed for deprecated APIs i.e. "Response Plays" to avoid breaking changes

**2025-09-24: 5.0.0: API authentication interface refactor**

In this version, the details of how authentication are performed are offloaded to a new class, ``AuthMethod``. Each instance of ``ApiClient`` have a new property, ``auth_method``, which is an instance of ``AuthMethod``. This provides a generic framework for implementing all the forms of authentication (using headers or parameters in the request body) utilized in all of PagerDuty's APIs, minimizing redundant code in ``ApiClient`` subclasses.

The primary motivation of this change was to make the behavior of REST API v2 client objects more stable and predictable when swapping out their API credentials mid-process. This is needed for the purposes of an internal project at PagerDuty.

* **Breaking Changes:**
   - The ``api_key`` property has been removed from all client classes except for ``pagerduty.RestApiV2BaseClient`` and subclasses thereof, wherein it is deprecated.
   - The hook method ``after_set_api_key`` will be ignored in all classes where the ``api_key`` property has been removed.

**2025-09-08: 4.1.1: Bugfix: iter_all parameter serialization**

* Fixes a regression wherein a boolean is serialized to the capitalized ``True`` / ``False`` for the ``total`` parameter in classic pagination, whereas the API requires lower case values.

**2025-08-27: 4.1.0: Feature: PKCE OAuth helpers**

* **Feature:** new methods ``get_new_token_from_code_with_pkce``, ``generate_s256_pkce_params`` and ``get_pkce_authorize_url`` of ``pagerduty.OAuthTokenClient`` to assist with implementation of the OAuth via PKCE token grant flow.

**2025-08-18: 4.0.1: Bugfix: export all features currently imported to the root namespace**

* **Fixes:** adds an explicit ``__all__`` declaration to the root ``pagerduty`` module namespace for all members that are currently imported to that namespace.

**2025-08-12: 4.0.0: REST API Base Client Refactor + New Clients**

* **Breaking Changes:**

   - Deprecated property ``RestApiV2Client.trunc_token`` has been removed.
   - Helper functions have been moved; any namespaced references to them will need to be updated. References to them in the root ``pagerduty`` namespace will not be affected; they are still imported there for backwards compatibility. The changes are as follows:

      * Helper functions ``last_4`` and ``normalize_url`` have been moved from ``pagerduty.api_client`` to ``pagerduty.common``.
      * Helper functions ``endpoint_matches``, ``is_path_param``, ``infer_entity_wrapper`` and ``unwrap`` have been moved from ``pagerduty.rest_api_v2_client`` to ``pagerduty.rest_api_v2_base_client``.
      * Function decorators ``auto_json``, ``resource_url`` and ``wrapped_entities`` have been moved from ``pagerduty.rest_api_v2_client`` to ``pagerduty.rest_api_v2_base_client``.

* **New Features:** API client classes for the integration APIs that share many of the same features of ``pagerduty.RestApiV2Client``:

   - ``pagerduty.SlackIntegrationApiClient`` and ``pagerduty.SlackIntegrationConnectionsApiClient`` provide support for the PagerDuty Slack Integration API.
   - ``pagerduty.MsTeamsIntegrationApiClient`` provides support for the PagerDuty MS Teams Integration API.
   - ``pagerduty.JiraServerIntegrationApiClient`` provides support for the PagerDuty Jira Server Integration API.
   - ``pagerduty.JiraCloudIntegrationApiClient`` provides support for the PagerDuty Jira Cloud Integration API.

* **Fixes and Refactoring:**

   - HTTP request headers:

      * Duplicate code has been removed from the ``prepare_headers`` method in all client classes and consolidated into ``pagerduty.ApiClient``.
      * The ``Content-Type`` header is now added when making ``PATCH`` requests in REST API v2.

   - New REST API base class ``pagerduty.RestApiV2BaseClient`` brings automatic entity wrapping and pagination helpers to new APIs outside of REST API v2
   - The ``total`` query parameter sent to the API by ``iter_all`` is now a boolean as it needs to be according to the API documentation.
   - New descriptive types for canonical paths and entity wrapping
   - The ``get_total`` method of REST API client classes now tests for a successful response before checking the response schema in order to raise the correct type of exception.

**2025-07-15: 3.1.0: New features**

* New features in ``RestApiV2Client``

   - Abstraction for endpoints that implement non-standard styles of pagination
   - Iterator method for incident notes
   - Method for testing if the account has a given ability

* Fix: Update the "Unknown version" (for versioned user-agent headers in Python prior to version 3.8) and add a test to validate that it is up to date with the true current major version

**2025-07-08: 3.0.0: New features**

* **Breaking Change:** the method ``ApiClient.normalize_params`` no longer modifies parameters. The implementation of it that previously did, which was meant only for the child class ``RestApiV2Client``, has been migrated to that class as an override.
* **New Features:**

   - New method ``OAuthTokenClient.refresh_client``: instantiates and returns a ``RestApiV2Client`` instance and auto-refreshes the access token
   - New method ``RestApiV2Client.iter_history``: iterates through large historical data sets that exceed the hard limit of classic pagination
   - New method ``RestApiV2Client.get_total``: returns the total number of matching records in a classic pagination endpoint
   - Expanded coverage of type hints
   - Documentantion revisions

* **Fixes:**

   - Method ``RestApiV2Client.rpatch`` now fully implemented (it mistakenly was left with no return value in previous versions)
   - Mutable default values in optional keyword arguments have been replaced with ``None``.

**2025-06-23: 2.3.0: Add a new OAuth token exchange client class**

* This version introduces a new client class for obtaining OAuth tokens using code grant / token refresh or for a scoped app.

**2025-06-03: 2.2.0: Add py.typed marker file**

* Add a ``py.typed`` marker file so that type checkers recognize that ``pagerduty`` supports type checking.

**2025-05-19: 2.1.2: Bug fixes for iter_cursor and HTTP 204 response handling**

* Allow ``try_decoding`` to return ``None`` for empty input; fixes GitHub issue #46.
* Non-breaking changes to ``RestApiV2Client.iter_cursor``, to fix GitHub issue #45:

   - It now uses the ``default_page_size`` client setting as the ``limit`` parameter.
   - It accepts a ``page_size`` parameter that can override said default (and ``params`` can also override this default), similar to ``iter_all``.
   - When called indirectly via ``iter_all``, the ``item_hook`` keyword argument is passed through to it, along with ``page_size``.

**2025-05-14: 2.1.1: Bug fix**

* The "main" method in the entry script is expected to receive no arguments, but in v2.1.0, it requires one positional argument.

**2025-05-13: 2.1.0: Command line interface**

* Add a basic command line interface for Events API v2, for feature parity with the legacy library that is used in the `Monit Integration Guide <https://www.pagerduty.com/docs/guides/monit-integration-guide/>`_.

**2025-04-08: 2.0.0: Multi-file refactor**

This release introduces major structural changes to the module and how it is built and tested. These changes were made for long-term maintainability of the codebase. Previously, it was all contained within a monolithic ``.py`` file (with a single Python script for all unit tests); now it is organized into smaller, appropriately-named Python files.

Some lesser changes are also included:

* The docstrings for the ``submit`` and ``send_change_event`` methods of ``EventsApiV2Client`` have been updated to reflect how they are expected to always return ``None``; this was causing Airflow build failures.
* The default user agent header has been updated: the prefix has been changed from ``pagerduty`` to ``python-pagerduty``.
* The version number ``pagerduty.__version__`` is now maintained in ``pyproject.toml`` and discovered through package metadata introspection at import time. In Python versions prior to 3.8, the version will be ``2.*.*`` because the new ``importlib`` feature required for it is unavailable.

**2025-01-02: 1.0.0: Migrate from PDPYRAS**

* **BREAKING CHANGE:** class names have changed from what they were in ``pdpyras``; see: `PDPYRAS Migration Guide <https://pagerduty.github.io/python-pagerduty/pdpyras_migration_guide.html>`_
* The REST API client now supports new status page, event orchestrations, custom incident fields, OAuth delegations and alert grouping settings APIs.

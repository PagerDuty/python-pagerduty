**2025-07-15: New features - Version 3.1.0**

* New features in ``RestApiV2Client``

   - Abstraction for endpoints that implement non-standard styles of pagination
   - Iterator method for incident notes
   - Method for testing if the account has a given ability

* Fix: Update the "Unknown version" (for versioned user-agent headers in Python prior to version 3.8) and add a test to validate that it is up to date with the true current major version

**2025-07-08: New features - Version 3.0.0**

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

**2025-06-23: Add a new OAuth token exchange client class - Version 2.3.0**

* This version introduces a new client class for obtaining OAuth tokens using code grant / token refresh or for a scoped app.

**2025-06-03: Add py.typed marker file - Version 2.2.0**

* Add a ``py.typed`` marker file so that type checkers recognize that ``pagerduty`` supports type checking.

**2025-05-19: Bug fixes for iter_cursor and HTTP 204 response handling - Version 2.1.2**

* Allow ``try_decoding`` to return ``None`` for empty input; fixes GitHub issue #46.
* Non-breaking changes to ``RestApiV2Client.iter_cursor``, to fix GitHub issue #45:

   - It now uses the ``default_page_size`` client setting as the ``limit`` parameter.
   - It accepts a ``page_size`` parameter that can override said default (and ``params`` can also override this default), similar to ``iter_all``.
   - When called indirectly via ``iter_all``, the ``item_hook`` keyword argument is passed through to it, along with ``page_size``.

**2025-05-14: Bug fix - Version 2.1.1**

* The "main" method in the entry script is expected to receive no arguments, but in v2.1.0, it requires one positional argument.

**2025-05-13: Command line interface - Version 2.1.0**

* Add a basic command line interface for Events API v2, for feature parity with the legacy library that is used in the `Monit Integration Guide <https://www.pagerduty.com/docs/guides/monit-integration-guide/>`_.

**2025-04-08: Multi-file refactor - Version 2.0.0**

This release introduces major structural changes to the module and how it is built and tested. These changes were made for long-term maintainability of the codebase. Previously, it was all contained within a monolithic ``.py`` file (with a single Python script for all unit tests); now it is organized into smaller, appropriately-named Python files.

Some lesser changes are also included:

* The docstrings for the ``submit`` and ``send_change_event`` methods of ``EventsApiV2Client`` have been updated to reflect how they are expected to always return ``None``; this was causing Airflow build failures.
* The default user agent header has been updated: the prefix has been changed from ``pagerduty`` to ``python-pagerduty``.
* The version number ``pagerduty.__version__`` is now maintained in ``pyproject.toml`` and discovered through package metadata introspection at import time. In Python versions prior to 3.8, the version will be ``2.*.*`` because the new ``importlib`` feature required for it is unavailable.

**2025-01-02: Migrate from PDPYRAS - Version 1.0.0**

* **BREAKING CHANGE:** class names have changed from what they were in ``pdpyras``; see: `PDPYRAS Migration Guide <https://pagerduty.github.io/python-pagerduty/pdpyras_migration_guide.html>`_
* The REST API client now supports new status page, event orchestrations, custom incident fields, OAuth delegations and alert grouping settings APIs.

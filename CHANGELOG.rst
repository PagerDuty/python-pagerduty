**2025-04-08: Multi-file refactor - Version 2.0.0**

This release introduces major structural changes to the module and how it is built and tested. These changes were made for long-term maintainability of the codebase. Previously, it was all contained within a monolithic ``.py`` file (with a single Python script for all unit tests); now it is organized into smaller, appropriately-named Python files.

Some lesser changes are also included:

* The docstrings for the ``submit`` and ``send_change_event`` methods of ``EventsApiV2Client`` have been updated to reflect how they are expected to always return ``None``; this was causing Airflow build failures.
* The default user agent header has been updated: the prefix has been changed from ``pagerduty`` to ``python-pagerduty``.
* The version number ``pagerduty.__version__`` is now maintained in ``pyproject.toml`` and discovered through package metadata introspection at import time. In Python versions prior to 3.8, the version will be ``2.*.*`` because the new ``importlib`` feature required for it is unavailable.

**2025-01-02: Migrate from PDPYRAS - Version 1.0.0**

* **BREAKING CHANGE:** class names have changed from what they were in ``pdpyras``; see: `PDPYRAS Migration Guide <https://pagerduty.github.io/python-pagerduty/pdpyras_migration_guide.html>`_
* The REST API client now supports new status page, event orchestrations, custom incident fields, OAuth delegations and alert grouping settings APIs.

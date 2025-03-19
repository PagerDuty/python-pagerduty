**2025-03-20: Multi-file refactor - Version 2.0.0**

A no-op with respect to features, this release includes major structural changes to the module and how it is built and tested.

These changes were made for long-term maintainability of the codebase, which previously was all contained within a single ``.py`` file.

**2025-01-02: Migrate from PDPYRAS - Version 1.0.0**

* **BREAKING CHANGE:** class names have changed from what they were in ``pdpyras``; see: `PDPYRAS Migration Guide <https://pagerduty.github.io/python-pagerduty/pdpyras_migration_guide.html>`_
* The REST API client now supports new status page, event orchestrations, custom incident fields, OAuth delegations and alert grouping settings APIs.

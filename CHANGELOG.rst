**2025-03-20: Multi-file refactor - Version 2.0.0**

* Major structural changes to the module and how it is built and tested. These changes were made for long-term maintainability of the codebase, which previously was all contained within a single ``.py`` file.
* Add a return statement originally in ``pdpyras`` back to a function (``EventsApiV2Client.send_change_event``) that is expected to always return ``None``.
* User-Agent header update: the prefix has been changed from ``pagerduty`` to ``python-pagerduty``.
* The version number ``pagerduty.__version__`` in Python versions prior to 3.8 is ``2.?.?-metadata-unavailable`` because the new ``importlib`` features that allow deriving the version number from package metadata are unavailable in those versions.

**2025-01-02: Migrate from PDPYRAS - Version 1.0.0**

* **BREAKING CHANGE:** class names have changed from what they were in ``pdpyras``; see: `PDPYRAS Migration Guide <https://pagerduty.github.io/python-pagerduty/pdpyras_migration_guide.html>`_
* The REST API client now supports new status page, event orchestrations, custom incident fields, OAuth delegations and alert grouping settings APIs.

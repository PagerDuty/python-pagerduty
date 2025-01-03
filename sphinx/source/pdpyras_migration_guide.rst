.. _pdpyras_migration_guide

=======================
PDPYRAS Migration Guide
=======================
In addition to renaming the module from ``pdpyras`` to ``pagerduty``, version
1.0 of ``python-pagerduty`` includes some forward-looking class name changes
from the original `pdpyras`_ source code. This was done so that nomenclature
clearly reflects the hierarchy of APIs and errors, and to make the relationship
between API clients and their respective APIs more clear.

Replacements are expressed in `sed-style substitution format
<https://www.gnu.org/software/sed/manual/html_node/The-_0022s_0022-Command.html>`_,
i.e. if replacing all instances of ``{{pattern}}`` with ``{{replacement}}``,
the pattern is ``s/{{pattern}}/{{replacement}}/g``.

The first substitution that should be made is ``s/pdpyras/pagerduty/g``, i.e.

::

    - import pdpyras
    + import pagerduty

Client Classes
--------------
In code that uses `pdpyras`_, the following class name replacements should be
made to switch to using their equivalents in `python-pagerduty`. **The first
three should be done in the order shown, so as to avoid name overlap issues:**

1. ``s/ChangeEventsAPISession/EventsApiV2Client/g``
2. ``s/EventsAPISession/EventsApiV2Client/g``
3. ``s/APISession/RestApiV2Client/g``
4. ``s/PDSession/ApiClient/g``

Note, the Change Events API client has been merged into the Events API v2 client
because the former API is effectively a component of the latter. The
differences are trivial enough to support both use cases with a single client
class, and there are no method or property name collisions between the two
original classes.

Exception Classes
-----------------
The exception classes have been renamed as follows:

* ``s/PDClientError/Error/g``
* ``s/PDServerError/ServerHttpError/g``
* ``s/PDHTTPError/HttpError/g``
* ``s/URLError/UrlError/g``

.. _`pdpyras`: https://github.com/PagerDuty/pdpyras

.. _pdpyras_migration_guide

=======================
PDPYRAS Migration Guide
=======================
In addition to renaming the module from ``pdpyras`` to ``pagerduty``, version
1.0 of ``python-pagerduty`` includes some forward-looking class name changes
from the original `pdpyras`_ source code. This was done so that nomenclature
clearly reflects the hierarchy of APIs and errors, and to make the relationship
between API clients and their respective APIs more clear.

The following replacements are expressed in `sed-style substitution format
<https://www.gnu.org/software/sed/manual/html_node/The-_0022s_0022-Command.html>`_,
i.e. if replacing all instances of ``{{pattern}}`` with ``{{replacement}}``:

::

   s/{{pattern}}/{{replacement}}/g


Client Classes
--------------
In downstream code that uses `pdpyras`_, the following name replacements
should be made in order to switch to using `python-pagerduty`. **The first
three should be done in the order shown, so as to avoid name overlap issues:**

1. ``s/ChangeEventsAPISession/EventsApiV2Client/g``
2. ``s/EventsAPISession/EventsApiV2Client/g``
3. ``s/APISession/RestApiV2Client/g``
4. ``s/PDSession/ApiClient/g``

Exception Classes
-----------------
The exception classes have been renamed as follows:

* ``s/PDClientError/Error/g``
* ``s/PDServerError/ServerHttpError/g``
* ``s/PDHTTPError/HttpError/g``
* ``s/URLError/UrlError/g``

.. _`pdpyras`: https://github.com/PagerDuty/pdpyras

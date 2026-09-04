==================
Contribution Guide
==================

Bug reports and pull requests to fix issues are always welcome, as are
contributions to the built-in documentation.

If adding features, or making changes, it is recommended to update or add tests
and assertions to the appropriate test case class in ``test_pagerduty.py`` to
ensure code coverage. If the change(s) fix a bug, please add assertions that
reproduce the bug along with code changes themselves, and include the GitHub
issue number in the commit message.


Initial Setup
-------------
To be able to rebuild the documentation, apply formatting and release new
versions, first make sure you have `make <https://www.gnu.org/software/make/>`_
installed in your local development environment, as well as
`uv <https://docs.astral.sh/uv/>`_ for dependency management.

Next, run ``test.sh`` in the root path of the repository to validate that unit
tests can be run locally.


Linting, Formatting and Testing
-------------------------------
All of the CI tests can be run locally, provided that all development
dependencies are installed locally.

**To run unit tests:** run ``make test``. To see all output from ``print``
statements in unit test cases, run ``./test.sh`` directly, or ``make
verbose-test``.

**Linting:** run ``make lint`` or ``uvx ruff check`` to run lint checks. To fix
issues automatically where possible, run ``make lint-fix`` or ``uvx ruff check
--fix``.

**Formatting:** run ``make format`` or ``uvf ruff format --check`` to check for code format
issues, and to fix automatically where possible, run ``make format-fix`` or
``uvx ruff format``.


Adding Support for New API Endpoints
------------------------------------
For the most part, the clients of ``python-pagerduty`` are agnostic to the API
schema and do not require modification for basic support of new APIs. The
instance methods that are named after HTTP request methods already support
arbitrary requests and can be used with experimental new endpoints, in addition
to the ``j*`` methods.

However, the features of clients built upon common patterns, i.e. pagination
support, must have knowledge of the key ("wrapper name") in the request or
response schema. When new endpoints are added, the client has no a-priori
knowledge of them, and supporting them with these conveniences requries a few
small changes. The system in place for supporting endpoints requires the
following variables in ``pagerduty/rest_api_v2_client.py`` be manually
maintained:

* ``CANONICAL_PATHS``, the list of canonical paths;
* ``CURSOR_BASED_PAGINATION_PATHS``, a list of canonical paths that support cursor-based pagination
* ``ENTITY_WRAPPER_CONFIG``, a dictionary of exceptions to entity wrapping and schema conventions

For any APIs defined outside of the bounds of REST API v2 (as structured in the
API references), but that use similar patterns to REST API v2, there are
separate API client classes defined for them based on ``RestApiV2BaseClient``,
namespaced within ther own modules. The modules also contain their own
definitions for ``CANONICAL_PATHS``, ``ENTITY_WRAPPER_CONFIG`` and
``CURSOR_BASED_PAGINATION_PATHS`` that are used for those APIs.


Adding a New Client Class
*************************
When evaluating a new API, the first question to ask is whether the new API
resides within the scope of the existing REST API. This is addressed in the
user guide ("Which Client Class To Use"); to recap, if it's documented under
"PagerDuty API", it will be accessed using :attr:`pagerduty.RestApiV2Client`;
otherwise, it requires a different client class.  The new endpoints should
follow all the same basic conventions for authentication and access, i.e. use
the standard ``api.pagerduty.com`` server hostname.

If the new API is very similar in function to the REST API but is documented as
a separate new API, i.e. it features pagination endpoints, the client can be
designed as a child class of :attr:`pagerduty.RestApiV2BaseClient`. Refer to
existing derivative classes, i.e. the "Integration" API clients, for examples.

If any new API endpoint is documented within the REST API, but breaks out of
these conventions, i.e.

* Uses a new and different form of authentication
* Does not support all forms of authentication (token and OAuth / Bearer) supported by other REST API endpoints
* Uses a different host name than ``api.pagerduty.com`` for one or more of its endpoints
* Uses any format other than JSON to encode content

Then the new API has been erroneously added to the standard REST API, and it
should instead be added as a separate new top-level API, and it cannot be
supported by the existing REST API client. Contact PagerDuty support or the
appropriate engineering team about documenting it as a new API distinct from
REST API v2. It cannot be treated as part of the standard REST API because its
requirements for use contradict the instructions for API access documented
generally for all other REST API endpoints.


Updating the Canonical Path Set
*******************************
First, to add support for new REST API endpoints, have an updated clone of the API Reference
source code repository (this is a private GitHub repository owned by the PagerDuty org).
Next, run the script:

.. code-block:: bash

    ./scripts/get_path_list/get_path_list.py [PATH-TO-REPOSITORY]/reference/v2/Index.yaml

This script will print definitions of the global variables ``CANONICAL_PATHS``
and ``CURSOR_BASED_PAGINATION_PATHS`` for ``pagerduty/rest_api_v2_client.py``,
i.e. that can be copied into the source code to replace the existing
definitions.


Evaluating New REST API Endpoints
*********************************
The next step is to look at the request and response schemas in the API
reference for each new endpoint added to the canonical path list, to see if it
follows classic schema conventions for entity wrapping. If any new path does
not, adding support for it will also require adding entries to the
``ENTITY_WRAPPER_CONFIG`` dictionary defined in the client's module (see
"Antipattern Endpoints" below). "Classic schema conventions" refers to the
logic codified in :attr:`pagerduty.rest_api_v2_base_client.infer_entity_wrapper` and
:attr:`pagerduty.rest_api_v2_base_client.unwrap` (where a "node" is a component of the path component
of the URL, separated by forward slashes):

**1:** If the last node of the path is an opaque identifier, then the path corresponds
to an individual PagerDuty resource, and the request and response wrapper names
are both the singular form of the second-to-last node. Examples: ``PUT
/escalation_policies/{id}`` (wrapper = ``escalation_policy``), ``GET
/users/{id}`` (wrapper = ``user``).

**2:** If the last node of the path is not an opaque identifier, and the
request method is POST, then the request and response wrapper names are both
the singular form of the last node. Examples: ``POST /schedules`` (wrapper =
``schedule``), ``POST /incidents`` (wrapper = ``incident``)

**3:** Otherwise (the last node of the path is not an opaque identifier and the
request method is not POST), the request and response wrapper names are both
the same as the last node of the path. Examples: ``GET /services`` (wrapper =
``services``), ``PUT /incidents`` (wrapper = ``incidents``)

If all of the above apply to new endpoints for all request methods, then no new
entries need to be added to ``ENTITY_WRAPPER_CONFIG`` to support them; they are
supported automatically by virtue of following preexisting already-supported
API patterns. Support for them is fully covered by adding the corresponding
entries in ``CANONICAL_PATHS``.

Adding Support for Antipattern Endpoints
****************************************
If the new endpoints do not follow classic schema conventions for entity
wrapping, entries for them must be added to the appropriate
``ENTITY_WRAPPER_CONFIG`` dictionary in the module corresponding to the API
client in question in order to support them.  In that dictionary, each key is a
combination of the request method (or ``*`` for the configuration entry to
apply to all methods) and the canonical path in question, and each value:

* Is a string value, to signify the same wrapper name in the request and response bodies,
* ``None`` if entity wrapping is not applicable (in which case pagination is not supported),
* A 2-tuple if the entity wrapping differs between the request and response bodies (where the first element is the request body wrapper, and the second is the response body wrapper)

Following the same examples as given in the :ref:`user_guide`: the entry in
``ENTITY_WRAPPER_CONFIG`` to handle the "Create Business Service Subscribers"
looks like this:

.. code-block:: python

    'POST /business_services/{id}/subscribers': ('subscribers', 'subscriptions'),


In other words, what this describes is that when making a ``POST`` request to
``/business_services/{id}/subscribers``, the JSON data of the request should be
wrapped in a root-level JSON attribute named ``subscribers``, and in the
response, the JSON data is wrapped in a root-level JSON attribute named
``subscriptions``.

To give another example, the "Create one or more overrides" API endpoint entry looks like this:

.. code-block:: python

    'POST /schedules/{id}/overrides': ('overrides', None),


In requests to that endpoint, the list of override objects must be nested
within an ``overrides`` property, but the response is a bare list at the root
level of the body after JSON-decoding.


Limitations to Pagination Support
*********************************
There are three main categories of antipatterns:

1. Entity wrapping is present but doesn't follow the original schema convention
2. There may or may not be wrapping but pagination is not implemented according to standards and requires its own special abstraction/interface
3. There is no entity wrapping

In the first case, If the endpoint's schema wraps entities but the wrapper name
doesn't follow from the path, entity wrapping can still be supported. If
classic pagination or cursor-based pagination is correctly implemented in the
new API, the automatic pagination methods can also support it once the
antipattern configuration entry is added.

However, if there is no entity wrapping, or pagination is not implemented
according to documented standards, automatic pagination cannot be supported for
the new resource collection endpoints.


Updating Documentation
----------------------

The ``.rst`` files in ``sphinx/source`` are where most of the documentation
lives. To rebuild the HTML documentation from the source, run:

.. code-block:: shell

    make docs

To force a rebuild, run ``touch CHANGELOG.rst`` first.

**NOTE:** Python version 3.13 or later must be used when rebuilding
documentation, or the version number in the documentation will be
``[V].?.?-metadata-unavailable``, where ``[V]`` is the current major version.

Releasing a New Version
-----------------------

For this process, you will need, at minimum:

* to run ``make build`` and commit changes to ``uv.lock`` before merging, to validate that building succeeds,
* the ability to create tags on the repository
* valid user accounts on both ``pypi.org`` and ``test.pypi.org`` that have the "Maintainer" role on the project, as well as the requirements installed (see above) and:
* `an API token <https://pypi.org/help/#apitoken>`_ to upload new releases to PyPI, with write access to the project.

To use a token for ``uv publish`` (which will be invoked in this process), set the
environment variable ``UV_PUBLISH_PASSWORD`` when running publish or
test-publish commands, i.e.

1. Run ``read -s UV_PUBLISH_PASSWORD`` to set the variable without echoing the token
2. Paste in the token and hit enter
3. Immediately afterwards, run ``export !$``

Perform end-to-end publish and installation testing
***************************************************

This series of tests may not always be necessary, but it is a good idea to
perform them when making significant or breaking changes. This testing step
will to ensure that installation and upgrading isn't broken, and thus help
avert a scenario where we have to yank a version because it breaks projects.

To test publishing and installing from the package index, first make sure you
have a valid user account on ``test.pypi.org`` that has publisher access to the
project as on ``pypi.org``. When ready to begin, set the environemnt variable
token for the test index as instructed above (it will differ from the live
``pypi.org`` index).

Note, once a release is uploaded, it is no longer possible to upload a release
with the same version number, even if that release is deleted. For that reason,
it is a good idea to first add a suffix that can be arbitrarily updated to
iterate, i.e.  ``-rc1``, to the version in ``pyproject.toml`` while testing,
and then revert the changes (including changes to ``uv.lock``) when done.

Once the above is done, to perform end-to-end tests, run ``make testpublish``,
which will perform the following:

* Build the Python package at the test version
* Upload the new arbitrary version to ``test.pypi.org``
* Test-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv that does not already have the library installed, to test
  installing for the first time
* Test-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv where the mainline library version is already installed, to test
  upgrading an existing install.

The script should print out the test version and success messages. Errors
should be investigated and mitigated before publishing. To test again,
temporarily change the version in ``pyproject.toml`` so that it counts as a new
release and gets uploaded. Be sure to remember to set it back to the desired
final version before the actual release, and revert any changes to ``uv.lock``.

Merge changes and tag
*********************

A pull request for releasing a new version should be created, which along with
the functional changes should also include at least:

* An update to ``CHANGELOG.rst`` describing the changes in the new release
* A change in the version number in ``pyproject.toml`` to a new
  version that follows `Semantic Versioning <https://semver.org/>`_.
* Rebuilt HTML documentation via ``make docs``.

After rebuilding the documentation, it can then be viewed by opening the file
``docs/index.html`` in a web browser. Including rebuilt documentation avoids
the need for a follow-up pull request with a doc rebuild, but also helps
reviewers by not requiring them to have the documentation-building tools.

Remember to commit any changes to ``docs/`` and ``uv.lock`` before merging.

Once the pull request is approved, merge. Then (locally) checkout main and tag,
with the format ``v{version}``, i.e. ``v6.1.0``, and push the tag i.e. with
``git push --tags``.

Publishing
**********

Once the changes are merged and tagged, make sure your local repository clone
has the ``main`` branch checked out at the latest available commit, and the
local file tree is clean (has no uncommitted changes). Then, set the publish
token environment variable as described above and run:

.. code-block:: shell

    make publish

Finally, `create a new release
<https://github.com/PagerDuty/pagerduty/releases/new>`_, and select the latest tag.
details:

* Select "Choose a tag" and select the new latest tag.
* If a new patch version is being released, update the existing release for
  that major and minor version.
.. _`pdpyras`: https://github.com/PagerDuty/pdpyras

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

Initial Setup and Unit Tests
----------------------------
To be able to rebuild the documentation, apply formatting and release new
versions, first make sure you have `make <https://www.gnu.org/software/make/>`_
installed in your local development environment, as well as
[uv](https://docs.astral.sh/uv/) for dependency management.

Next, run ``test.sh`` in the root path of the repository to validate that unit
tests can be run locally.

Maintaining Entity Wrapper Configuration
----------------------------------------
Typically, but not for all endpoints, the key ("wrapper name") in the request
or response schema can be inferred from the last or second to last node of the
endpoint URL's path. The wrapper name is a singular noun for an individual
resource or plural for a collection of resources.

When new endpoints are added to REST API v2, and they don't follow this
orthodox schema pattern, the client's pagination and entity wrapping methods
have no a-priori way of supporting them because the wrapper name cannot be
inferred from the endpoint path.

Introduction
************
To support the growing list of schema antipatterns in the PagerDuty product
REST API v2, a system was created (originally in `pdpyras`_ version 5.0.0) to
work around them and codify the deviations from orthodox patterns with minimal
hard-coded changes to the client. This system works by identifying endpoints
according to their "canonical path", that is to say the path portion of the
endpoint URL with ``{name}`` placeholders for variable/identifiers. The
canonical path is then used as an identifier to perform a hash lookup of
antipattern-handling configuration.

This system requires two global variables that must be manually maintained:

* :attr:`pagerduty.rest_api_v2_client.CANONICAL_PATHS`, the list of canonical paths
* :attr:`pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG`, a dictionary of exceptions to entity wrapping and schema conventions

Limitations
***********
There are three main categories of antipatterns:

1. Entity wrapping is present but doesn't follow the original schema convention
2. There may or may not be wrapping but pagination is not implemented according to standards
3. There is no entity wrapping

In the first case, If the endpoint's schema wraps entities but the wrapper name
doesn't follow from the path, entity wrapping can still be supported. If
classic pagination or cursor-based pagination is correctly implemented in the
new API, the automatic pagination methods can also support it once the
antipattern configuration entry is added.

However, if there is no entity wrapping, or pagination is not implemented
according to documented standards, automatic pagination cannot be supported for
resource collection endpoints.

Updating the Canonical Path Set
*******************************
The first step for adding support for new APIs is to have a copy of the API
Reference source code (this is a private GitHub repository owned by the
PagerDuty org). The script ``scripts/get_path_list/get_path_list.py`` can then
be used to automatically generate definitions of the global variables
:attr:`pagerduty.rest_api_v2_client.CANONICAL_PATHS` and
:attr:`pagerduty.rest_api_v2_client.CURSOR_BASED_PAGINATION_PATHS` that can be copied into the
source code to replace the existing definitions. The script takes one argument:
a path to the file ``reference/v2/Index.yaml`` within the reference source
repository.

Evaluating New Endpoints For Support
************************************
The next step is to look at the request and response schemas in the API
reference for each new endpoint added to the canonical path list, to see if it
follows classic schema conventions for entity wrapping. If any new path does
not, adding support for it will also require adding entries to
:attr:`pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG`. "Classic schema conventions" refers to
the logic codified in :attr:`pagerduty.infer_entity_wrapper` and
:attr:`pagerduty.unwrap` (where a "node" is a component of the path component
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
entries need to be added to
:attr:`pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG` to support them;
they are supported automatically by virtue of following preexisting
already-supported API patterns. Their corresponding entries in
:attr:`pagerduty.rest_api_v2_client.CANONICAL_PATHS` officiates their support
for entity-wrapping-aware functions.

Adding Support for Non-Conforming Endpoints
*******************************************
If the new endpoints do not follow classic schema conventions for entity
wrapping, entries for them must be added to
:attr:`pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG` in order to support them. As described
in the documentation of that attribute, each key is a combination of the
request method (or "*" for the configuration entry to apply to all methods) and
the canonical path in question, and each value is a string (for the same
wrapper name in the request and response bodies), ``None`` if entity wrapping
is not applicable, and a tuple if the entity wrapping differs between the
request and response bodies.

Following the same examples as given in the :ref:`user_guide`: the entry in
:attr:`pagerduty.rest_api_v2_client.ENTITY_WRAPPER_CONFIG` to handle the "Create Business Service
Subscribers" looks like this:

.. code-block:: python

    'POST /business_services/{id}/subscribers': ('subscribers', 'subscriptions'),

The "Create one or more overrides" API endpoint entry looks like this:

.. code-block:: python

    'POST /schedules/{id}/overrides': ('overrides', None),

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

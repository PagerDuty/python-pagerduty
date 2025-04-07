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
To be able to rebuild the documentation and release a new version, first make
sure you have `make <https://www.gnu.org/software/make/>`_ and `pip
<https://pip.pypa.io/en/stable/installation/>`_ installed in your shell
environment, as well as Python version 3.11 or later.

The recommended way of setting up the Python environment is using `asdf-vm
<https://asdf-vm.com/>`_, i.e. run ``asdf install`` in your clone of the
repository.

Next, install Python dependencies for building and publishing as well as
testing locally:

.. code-block:: shell

    pip install .
    pip install -r requirements-publish.txt 

If asdf-vm was used to install Python locally, run the following after the above:

.. code-block:: shell

    asdf reshim python

Finally, run ``test.sh`` in the root path of the repository to run the unit
test suite locally, or run this command by itself:

.. code-block:: shell

    python -m unittest discover -p '*_test.py' -s tests

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

* :attr:`pagerduty.CANONICAL_PATHS`, the list of canonical paths
* :attr:`pagerduty.ENTITY_WRAPPER_CONFIG`, a dictionary of exceptions to entity wrapping and schema conventions

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
:attr:`pagerduty.CANONICAL_PATHS` and
:attr:`pagerduty.CURSOR_BASED_PAGINATION_PATHS` that can be copied into the
source code to replace the existing definitions. The script takes one argument:
a path to the file ``reference/v2/Index.yaml`` within the reference source
repository.

Evaluating New Endpoints For Support
************************************
The next step is to look at the request and response schemas in the API
reference for each new endpoint added to the canonical path list, to see if it
follows classic schema conventions for entity wrapping. If any new path does
not, adding support for it will also require adding entries to
:attr:`pagerduty.ENTITY_WRAPPER_CONFIG`. "Classic schema conventions" refers to
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
entries need to be added to :attr:`pagerduty.ENTITY_WRAPPER_CONFIG` to support
them; they are supported automatically by virtue of following preexisting
already-supported API patterns and having corresponding entries in
:attr:`pagerduty.CANONICAL_PATHS`.

Adding Support for Non-Conforming Endpoints
*******************************************
If the new endpoints do not follow classic schema conventions for entity
wrapping, entries for them must be added to
:attr:`pagerduty.ENTITY_WRAPPER_CONFIG` in order to support them. As described
in the documentation of that attribute, each key is a combination of the
request method (or "*" for the configuration entry to apply to all methods) and
the canonical path in question, and each value is a string (for the same
wrapper name in the request and response bodies), ``None`` if entity wrapping
is not applicable, and a tuple if the entity wrapping differs between the
request and response bodies.

Following the same examples as given in the :ref:`user_guide`: the entry in
:attr:`pagerduty.ENTITY_WRAPPER_CONFIG` to handle the "Create Business Service
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
``2.?.?-metadata-unavailable``.

Releasing a New Version
-----------------------

You will need valid user accounts on both ``pypi.org`` and ``test.pypi.org``
that have the "Maintainer" role on the project, as well as the requirements
installed (see above).

It is strongly recommended that you `use an API token
<https://pypi.org/help/#apitoken>`_ to upload new releases to PyPI. The token
must have write access to the project.

Perform end-to-end publish and installation testing
***************************************************

To test publishing and installing from the package index, first make sure you
have a valid user account on ``test.pypi.org`` that has publisher access to the
project as on ``pypi.org``.

Note, once a release is uploaded, it is no longer possible to upload a release
with the same version number, even if that release is deleted. For that reason,
it is a good idea to first add a suffix, i.e. ``-dev001``, to the version in
``pyproject.toml`` while testing.

To perform end-to-end tests, run the following, entering credentials for
``test.pypi.org`` when prompted:

.. code-block:: shell

    make testpublish

The make target ``testpublish`` performs the following:

* Build the Python package
* Upload the new library to ``test.pypi.org``
* Test-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv that does not already have the library installed, to test
  installing for the first time
* Tests-install the library from ``test.pypi.org`` into a temporary Python
  virtualenv where the library is already installed, to test upgrading

If any errors are encountered, the script should immediately exit. Errors
should be investigated and mitigated before publishing. To test again,
temporarily change the version in ``pyproject.toml`` so that it counts as a new
release and gets uploaded, and set it to the desired version before the actual
release.

Merge changes and tag
*********************

A pull request for releasing a new version should be created, which along with
the functional changes should also include at least:

* An update to ``CHANGELOG.rst`` describing the changes in the new release
* A change in the version number in ``pyproject.toml`` to a new
  version that follows `Semantic Versioning <https://semver.org/>`_.
* Rebuilt HTML documentation

The HTML documentation can be rebuilt with the ``docs`` make target:

.. code-block:: shell

    make docs

After rebuilding the documentation, it can then be viewed by opening the file
``docs/index.html`` in a web browser. Including rebuilt documentation helps
reviewers by not requiring them to have the documentation-building tools
installed.

Once the pull request is approved, merge. Then (locally) checkout main and tag:

.. code-block:: shell

    git checkout main && \
      git pull origin main && \
      git tag "v$(python -c 'from pagerduty import __version__; print(__version__)')" && \
      git push --tags origin main

Publishing
**********

Once the changes are merged and tagged, make sure your local repository clone
has the ``main`` branch checked out at the latest available commit, and the
local file tree is clean (has no uncommitted changes). Then run:

.. code-block:: shell

    make publish

When prompted, enter ``__token__`` as your username and your API token as the password.

Finally, `create a new release
<https://github.com/PagerDuty/pagerduty/releases/new>`_, and fill in some
details:

* Select "Choose a tag" and select the new latest tag.
* If a new patch version is being released, update the existing release for
  that major and minor version.
* Name the release after the major and minor version, i.e. 5.1, and very brief
  summary of changes.
* Compose a description from the pull requests whose changes are included.

.. _`pdpyras`: https://github.com/PagerDuty/pdpyras

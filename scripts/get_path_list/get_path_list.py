#!/usr/bin/env python

"""
Usage: get_path_list.py PATH

  Generates a CANONICAL_PATHS attribute declaration for updating the client source code.

  PATH must be a path to "reference/v2/Index.yaml" within a clone of the API reference
  source code repository to re-generate canonical paths for REST API v2. One can also
  replace "v2" with the name of the "REST-ish" API within the "reference" directory,
  i.e. integration-slack-service, to generate CANONICAL_PATHS for the desired subclass
  of GenericRestIshApiClient.
"""

# This script is not part of the python-pagerduty library. Rather, it can be used for
# the by PagerDuty engineers to assist with its development and maintenance.  It
# automatically generates the declaration of module variables "ENDPOINT_PATTERNS" and
# "CURSOR_BASED_ITERATION_ENDPOINTS" from the API documentation source code (which is
# kept in a private repository in the
# PagerDuty GitHub org).
#
# It is meant to minimize the amount of work that has to be done to allow the REST API
# v2 client to support new APIs by generating the client's specific knowledge of APIs
# directly from the documentation programatically.

# NOTE:
#
# If any new API introduces an endpoint that is designed to work as a resource
# collection and support pagination, but whose path ends in a variable parameter
# that refers to a value in a fixed list of well-recognized entity types (as
# opposed to a separate documentation page per distinct entity type), THE
# CANONICAL PATH WILL NEED TO BE ADDED TO THE FOLLOWING DICTIONARY, OR ENTITY
# WRAPPING WILL END UP BROKEN FOR THAT ENDPOINT:
EXPAND_PATHS = {
    '/tags/{id}/{entity_type}': [
        '/tags/{id}/'+et for et in ('users', 'teams', 'escalation_policies')
    ]
}

import sys
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    file = sys.argv[1]
    api_ref = load(open(file, 'r'), Loader)
    public_endpoints = list(map(lambda kv: kv[0], filter(
        lambda kv: not kv[1].get('x-pd-private', False),
        api_ref['paths'].items()
    )))
    public_endpoints_dict = dict(map(lambda kv: (kv[0], kv[1]), filter(
        lambda kv: not kv[1].get('x-pd-private', False),
        api_ref['paths'].items()
    )))

    print('    CANONICAL_PATHS = [')
    for path in public_endpoints:
        print_paths = EXPAND_PATHS.get(path, [path])
        for path in print_paths:
            print(f"        '{path}',")
    print("    ]")
    print('    """'+"\n    Explicit list of supported canonical paths")
    print("\n    :meta hide-value:\n"+'    """'+"\n")

    print('    CURSOR_BASED_PAGINATION_PATHS = [')
    cursor_param_ref = '../common/models/Parameters.yaml#/cursor_cursor'
    for (path, spec) in public_endpoints_dict.items():
        getspec = spec.get('get', {})
        getparams = getspec.get('parameters', [])
        for param in getparams:
            if cursor_param_ref in param.values():
                print(f"        '{path}',")
    print('    ]')
    print('    """'+"\n    Explicit list of paths that support cursor-based pagination")
    print("\n    :meta hide-value:\n"+'    """')


if __name__ == '__main__':
    main()

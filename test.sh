#!/bin/bash

if [ ! -z $SUPPRESS_OUTPUT ]; then
  UNITTEST_OPTIONS="-b ${UNITTEST_OPTIONS:-}"
fi
uv run /usr/bin/env python3 -m unittest discover -p '*_test.py' -s tests $UNITTEST_OPTIONS

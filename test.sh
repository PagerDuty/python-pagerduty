#!/bin/bash

if [ "${NO_UV:-0}" == 1 ]; then
  echo "Using backwards compatibility hack for Python < 3.8 (using pip/virtualenv; uv_build unavailable)"
  virtualenv .python
  . .python/bin/activate
  which python
  python -V
  which pip
  pip -V

  pip install -r requirements.txt
  EXE=""
else
  EXE="uv run"
fi

$EXE /usr/bin/env python3 -m unittest discover -p '*_test.py' -s tests

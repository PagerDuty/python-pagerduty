#!/bin/bash

if [ "${NO_UV:-0}" == 1 ]; then
  # uv_build unavailable; install dependencies first
  virtualenv .python
  . .python/bin/activate
  which python
  python -V
  which pip
  pip -V

  echo "Using backwards compatibility hack for Python < 3.8 (no uv_build)"
  pip install -r requirements.txt
  EXE=""
else
  EXE="uv run"
fi

$EXE /usr/bin/env python3 -m unittest discover -p '*_test.py' -s tests

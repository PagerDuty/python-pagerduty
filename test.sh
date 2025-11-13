#!/bin/bash

if [ "${NO_UV:-0}" == 1 ]; then
  # UV unavailable; install dependencies first
  virtualenv .python
  . .python/bin/activate
  which python
  python -V
  which pip
  pip -V

  py_minor_ver=`python -c 'import sys; print(sys.version_info.minor)'`
  py_major_ver=`python -c 'import sys; print(sys.version_info.major)'`

  if [[ $py_major_ver -le 3 ]]; then
    if [[ $py_minor_ver -le 6 ]]; then
      echo "Using backwards compatibility hack for Python 3.6"
      pip install -r requirements.txt
    else
      echo "pip install ."
      pip install .
    fi
  fi
  EXE=""
else
  EXE="uv run"
fi

$EXE /usr/bin/env python3 -m unittest discover -p '*_test.py' -s tests

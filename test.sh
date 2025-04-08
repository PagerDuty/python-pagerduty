#!/bin/bash

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

/usr/bin/env python3 -m unittest discover -p '*_test.py' -s tests

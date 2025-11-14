#!/bin/bash
set -e

PACKAGE='pagerduty'
VERSION=`grep '^version' pyproject.toml | cut -d'"' -f2 | head -n 1`

refresh_virtualenv () {
    echo "--- Re-creating temporary virtualenv"
    rm -rf ./tmp
    mkdir -p ./tmp
    uv run virtualenv ./tmp >/dev/null 2>&1
}

py_test () {
  echo "--- Using Python: `which python`"
  python - <<EOF
import sys
if '${PACKAGE}' in sys.modules:
  del sys.modules['${PACKAGE}']
import ${PACKAGE}
print(${PACKAGE}.__version__)
print(${PACKAGE}.__file__)
EOF
  [[ $? == 0 ]] && echo "--- Success!" || echo "--- Failure."
}

echo "--- Testing publish / test install ${PACKAGE}==${VERSION}"

if [[ "${SKIP_UPLOAD:-0}" == "0" ]]; then
  echo "--- Uploading to test.pypi.org"
  uv publish --indexpublish-url 'https://test.pypi.org/legacy/' --username __token__
fi

echo "--- Testing install from scratch"
refresh_virtualenv
pushd ./tmp
source ./bin/activate
echo "--- Using pip: `which pip`"
# This hack is necessary because httpx is not present in the test index:
pip install -r ../requirements.txt 
pip install --index-url https://test.pypi.org/simple/ "${PACKAGE}==${VERSION}"
py_test
deactivate
popd

echo "--- Testing install of mainline version and then upgrade from testing index"
refresh_virtualenv
pushd ./tmp
source ./bin/activate
echo "--- Using pip: `which pip`"
pip install pagerduty
pip install --upgrade --index-url https://test.pypi.org/simple/ "${PACKAGE}==${VERSION}"
py_test
deactivate
popd
rm -rf tmp

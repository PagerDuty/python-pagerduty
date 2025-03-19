#!/usr/bin/env python

"""
Unit tests for pagerduty

Python 3, or the backport of unittest.mock for Python 2, is required.

See:

https://docs.python.org/3.5/library/unittest.mock.html
https://pypi.org/project/backports.unittest_mock/1.3/
"""
import argparse
import sys
import unittest

# Allows importing the pagerduty module locally:
sys.path.append('..')

from common_test import UrlHandlingTest, HelperFunctionsTest
from events_api_v2_client_test import EventsApiV2ClientTest
from rest_api_v2_client_test import (
    RestApiV2UrlHandlingTest,
    EntityWrappingTest,
    RestApiV2ClientTest
)

def main():
    ap=argparse.ArgumentParser()
    unittest.main()

if __name__ == '__main__':
    main()

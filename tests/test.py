#!/usr/bin/env python

"""
Unit tests for pagerduty
"""
import argparse
import sys
import unittest

# Allows importing the pagerduty module locally:
sys.path.append('..')

from common_test import (
    UrlHandlingTest,
    HelperFunctionsTest
)
from events_api_v2_client_test import EventsApiV2ClientTest
from rest_api_v2_client_test import (
    RestApiV2UrlHandlingTest,
    EntityWrappingTest,
    FunctionDecoratorsTest,
    RestApiV2ClientTest
)

def main():
    ap=argparse.ArgumentParser()
    unittest.main()

if __name__ == '__main__':
    main()

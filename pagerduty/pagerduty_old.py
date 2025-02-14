
# Copyright (c) PagerDuty.
# See LICENSE for details.

# Standard libraries
import logging
import sys
import time
from copy import deepcopy
from datetime import datetime
from random import random
from typing import Iterator, Union
from warnings import warn

# Upstream components on which this client is based:
from requests import Response, Session
from requests import __version__ as REQUESTS_VERSION

# HTTP client exceptions:
from urllib3.exceptions import HTTPError, PoolError
from requests.exceptions import RequestException

__version__ = '1.0.0'

#######################
### CLIENT DEFAULTS ###
#######################

####################
### URL HANDLING ###
####################

###########################
### FUNCTION DECORATORS ###
###########################

###############
### CLASSES ###
###############


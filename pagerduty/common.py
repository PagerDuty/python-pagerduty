# Core
from typing import Union
from warnings import warn

# PyPI
from requests import Response

########################
### DEFAULT SETTINGS ###
########################

TEXT_LEN_LIMIT = 100
"""
The longest permissible length of API content to include in error messages.
"""

########################
### HELPER FUNCTIONS ###
########################

def auto_json(method):
    """
    Makes methods return the full response body object after decoding from JSON.

    Intended for use on functions that take a URL positional argument followed
    by keyword arguments and return a `requests.Response`_ object.
    """
    doc = method.__doc__
    def call(self, url, **kw):
        return try_decoding(successful_response(method(self, url, **kw)))
    call.__doc__ = doc
    return call

def deprecated_kwarg(deprecated_name: str, details=None, method=None):
    """
    Raises a warning if a deprecated keyword argument is used.

    :param deprecated_name: The name of the deprecated function
    :param details: An optional message to append to the deprecation message
    :param method: An optional method name
    """
    details_msg = ''
    method_msg = ''
    if method is not None:
        method_msg = f" of {method}"
    if details is not None:
        details_msg = f" {details}"
    warn(
        f"Keyword argument \"{deprecated_name}\"{method_msg} is deprecated."+details_msg
    )

def http_error_message(r: Response, context=None) -> str:
    """
    Formats a message describing a HTTP error.

    :param r:
        The response object.
    :param context:
        A description of when the error was received, or None to not include it
    :returns:
        The message to include in the HTTP error
    """
    received_http_response = bool(r.status_code)
    endpoint = "%s %s"%(r.request.method.upper(), r.request.url)
    context_msg = ""
    if type(context) is str:
        context_msg=f" in {context}"
    if received_http_response and not r.ok:
        err_type = 'unknown'
        if r.status_code / 100 == 4:
            err_type = 'client'
        elif r.status_code / 100 == 5:
            err_type = 'server'
        tr_bod = truncate_text(r.text)
        return f"{endpoint}: API responded with {err_type} error (status " \
            f"{r.status_code}){context_msg}: {tr_bod}"
    elif not received_http_response:
        return f"{endpoint}: Network or other unknown error{context_msg}"
    else:
        return f"{endpoint}: Success (status {r.status_code}) but an " \
            f"expectation still failed{context_msg}"

def plural_name(obj_type: str) -> str:
    """
    Pluralizes a name, i.e. the API name from the ``type`` property

    :param obj_type:
        The object type, i.e. ``user`` or ``user_reference``
    :returns:
        The name of the resource, i.e. the last part of the URL for the
        resource's index URL
    """
    if obj_type.endswith('_reference'):
        # Strip down to basic type if it's a reference
        obj_type = obj_type[:obj_type.index('_reference')]
    if obj_type.endswith('y'):
        # Because English
        return obj_type[:-1]+'ies'
    else:
        return obj_type+'s'

def requires_success(method):
    """
    Decorator that validates HTTP responses.
    """
    doc = method.__doc__
    def call(self, url, **kw):
        return successful_response(method(self, url, **kw))
    call.__doc__ = doc
    return call

def singular_name(r_name: str) -> str:
    """
    Singularizes a name, i.e. for the entity wrapper in a POST request

    :para r_name:
        The "resource" name, i.e. "escalation_policies", a plural noun that
        forms the part of the canonical path identifying what kind of resource
        lives in the collection there, for an API that follows classic wrapped
        entity naming patterns.
    :returns:
        The singularized name
    """
    if r_name.endswith('ies'):
        # Because English
        return r_name[:-3]+'y'
    else:
        return r_name.rstrip('s')

def successful_response(r: Response, context=None) -> Response:
    """Validates the response as successful.

    Returns the response if it was successful; otherwise, raises an exception.

    :param r:
        Response object corresponding to the response received.
    :param context:
        A description of when the HTTP request is happening, for error reporting
    :returns:
        The response object, if it was successful
    """
    if r.ok and bool(r.status_code):
        return r
    elif r.status_code / 100 == 5:
        raise ServerHttpError(http_error_message(r, context=context), r)
    elif bool(r.status_code):
        raise HttpError(http_error_message(r, context=context), r)
    else:
        raise Error(http_error_message(r, context=context))

def truncate_text(text: str) -> str:
    """Truncates a string longer than :attr:`TEXT_LEN_LIMIT`

    :param text: The string to truncate if longer than the limit.
    """
    if len(text) > TEXT_LEN_LIMIT:
        return text[:TEXT_LEN_LIMIT-1]+'...'
    else:
        return text

def try_decoding(r: Response) -> Union[dict, list, str]:
    """
    JSON-decode a response body

    Returns the decoded body if successful; raises :class:`ServerHttpError`
    otherwise.

    :param r:
        The response object
    """
    try:
        return r.json()
    except ValueError as e:
        raise ServerHttpError(
            "API responded with invalid JSON: " + truncate_text(r.text),
            r,
        )

##################
### EXCEPTIONS ###
##################

class UrlError(Exception):
    """
    Exception class for unsupported URLs or malformed input.
    """
    pass

class Error(Exception):
    """
    General API errors base class.

    Note, the name of this class does not imply it solely includes errors
    experienced by the client or HTTP status 4xx responses, but descendants can
    include issues with the API backend.
    """

    response = None
    """
    The HTTP response object, if a response was successfully received.

    In the case of network errors, this property will be None.
    """

    def __init__(self, message, response=None):
        self.msg = message
        self.response = response
        super(Error, self).__init__(message)

class HttpError(Error):
    """
    Error class representing errors strictly associated with HTTP responses.

    This class was created to make it easier to more cleanly handle errors by
    way of a class that is guaranteed to have its ``response`` be a valid
    `requests.Response`_ object.

    Whereas, the more generic :class:`Error` could also be used
    to denote such things as non-transient network errors wherein no response
    was recevied from the API.

    For instance, instead of this:

    ::

        try:
            user = session.rget('/users/PABC123')
        except pagerduty.Error as e:
            if e.response is not None:
                print("HTTP error: "+str(e.response.status_code))
            else:
                raise e

    one could write this:

    ::

        try:
            user = session.rget('/users/PABC123')
        except pagerduty.HttpError as e:
            print("HTTP error: "+str(e.response.status_code))
    """

    def __init__(self, message, response: Response):
        super(HttpError, self).__init__(message, response=response)

class ServerHttpError(HttpError):
    """
    Error class representing failed expectations made of the server.

    This is raised in cases where the response schema differs from the expected schema
    because of an API bug, or because it's an early access endpoint and changes before
    GA, or in cases of HTTP status 5xx where a successful response is required.
    """
    pass


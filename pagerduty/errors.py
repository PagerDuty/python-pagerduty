from requests import Response

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
    was received from the API.
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


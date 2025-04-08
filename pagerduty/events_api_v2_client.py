# Core
from copy import deepcopy
from datetime import datetime

# PyPI
from requests import Response

# Local
from . api_client import ApiClient
from . common import (
    deprecated_kwarg,
    successful_response,
    try_decoding,
    truncate_text
)

class EventsApiV2Client(ApiClient):

    """
    Session class for submitting events to the PagerDuty v2 Events API.

    Implements methods for submitting events to PagerDuty through the Events API,
    including change events, and inherits from :class:`pagerduty.ApiClient`.  For more
    details on usage of this API, refer to the `Events API v2 documentation
    <https://developer.pagerduty.com/docs/events-api-v2/overview/>`_
    """

    permitted_methods = ('POST',)

    url = "https://events.pagerduty.com"

    def __init__(self, api_key: str, debug=False):
        super(EventsApiV2Client, self).__init__(api_key, debug)
        # See: https://developer.pagerduty.com/docs/3d063fd4814a6-events-api-v2-overview#response-codes--retry-logic
        self.retry[500] = 2 # internal server error
        self.retry[502] = 4 # bad gateway
        self.retry[503] = 6 # service unavailable
        self.retry[504] = 6 # gateway timeout

    @property
    def auth_header(self) -> dict:
        return {}

    def acknowledge(self, dedup_key) -> str:
        """
        Acknowledge an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to set to the acknowledged state.
        :returns:
            The deduplication key
        """
        return self.send_event('acknowledge', dedup_key=dedup_key)

    @property
    def event_timestamp(self) -> str:
        return datetime.utcnow().isoformat()+'Z'

    def post(self, *args, **kw) -> Response:
        """
        Override of ``requests.Session.post``

        Adds the ``routing_key`` parameter to the body before sending.
        """
        if 'json' in kw and hasattr(kw['json'], 'update'):
            kw['json'].update({'routing_key': self.api_key})
        return super(EventsApiV2Client, self).post(*args, **kw)

    def prepare_headers(self, method, user_headers=None) -> dict:
        """
        Add user agent and content type headers for Events API requests.

        :param user_headers: User-supplied headers that will override defaults
        :returns:
            The final list of headers to use in the request
        """
        headers = {}
        headers.update(self.headers)
        headers.update({
            'Content-Type': 'application/json',
            'User-Agent': self.user_agent,
        })
        if user_headers is not None:
            headers.update(user_headers)
        return headers

    def resolve(self, dedup_key) -> str:
        """
        Resolve an alert via Events API.

        :param dedup_key:
            The deduplication key of the alert to resolve.
        """
        return self.send_event('resolve', dedup_key=dedup_key)

    def send_change_event(self, payload=None, links=None, routing_key=None):
        """
        Send a change event to the v2 Change Events API.

        See: https://developer.pagerduty.com/docs/events-api-v2/send-change-events/

        :param payload:
            A dictionary object with keys ``summary``, ``source``, ``timestamp`` and
            ``custom_details`` as described in the above documentation.
        :param links:
            A list of dictionary objects each with keys ``href`` and ``text``
            representing the target and display text of each link
        :param routing_key:
            (Deprecated) the routing key. The parameter is set automatically to the
            :attr:`ApiClient.api_key` property in the final payload and this argument is ignored.
        """
        if payload is None:
            payload = {}
        if links is None:
            links = []
        if routing_key is not None:
            deprecated_kwarg(
                'routing_key',
                method='EventsApiV2Client.send_change_event'
            )
        event = {'payload': deepcopy(payload)}
        if links:
            event['links'] = deepcopy(links)
        successful_response(
            self.post('/v2/change/enqueue', json=event),
            context="submitting change event",
        )

    def send_event(self, action, dedup_key=None, **properties) -> str:
        """
        Send an event to the v2 Events API.

        See: https://v2.developer.pagerduty.com/docs/send-an-event-events-api-v2

        :param action:
            The action to perform through the Events API: trigger, acknowledge
            or resolve.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param **properties:
            Additional properties to set, i.e. if ``action`` is ``trigger``
            this would include ``payload``.
        :type action: str
        :type dedup_key: str
        :returns:
            The deduplication key of the incident
        """

        actions = ('trigger', 'acknowledge', 'resolve')
        if action not in actions:
            raise ValueError("Event action must be one of: "+', '.join(actions))

        event = {'event_action':action}

        event.update(properties)
        if isinstance(dedup_key, str):
            event['dedup_key'] = dedup_key
        elif not action == 'trigger':
            raise ValueError("The dedup_key property is required for"
                "event_action=%s events, and it must be a string."%action)
        response = successful_response(
            self.post('/v2/enqueue', json=event),
            context='submitting an event to the events API',
        )
        response_body = try_decoding(response)
        if type(response_body) is not dict or 'dedup_key' not in response_body:
            err_msg = 'Malformed response body from the events API; it is ' \
                'not a dict that has a key named "dedup_key" after ' \
                'decoding. Body = '+truncate_text(response.text)
            raise ServerHttpError(err_msg, response)
        return response_body['dedup_key']

    def submit(self, summary, source=None, custom_details=None, links=None,
            timestamp=None):
        """
        Submit a change event.

        See: https://developer.pagerduty.com/docs/send-change-event

        This is a wrapper method for :attr:`send_change_event` that composes an event
        payload from keyword arguments and an auto-generated event timestamp. To send an
        event with a wholly custom payload, use :attr:`send_change_event` instead.

        :param summary:
            Summary / brief description of the change, for ``payload.summary``.
        :param source:
            A human-readable name identifying the source of the change, for the
            ``payload.source`` event property.
        :param custom_details:
            A dictionary object to use as the ``payload.custom_details`` property.
        :param links:
            A list of dict objects to use as the ``links`` property of the event.
        :param timestamp:
            Specifies an event timestamp. Must be an ISO8601-format date/time.
        :type summary: str
        :type source: str
        :type custom_details: dict
        :type links: list
        :type timestamp: str
        """
        local_var = locals()['custom_details']
        if not (local_var is None or isinstance(local_var, dict)):
            raise ValueError("custom_details must be a dict")
        if timestamp is None:
            timestamp = self.event_timestamp
        event = {
                'payload': {
                    'summary': summary,
                    'timestamp': timestamp,
                    }
                }
        if isinstance(source, str):
            event['payload']['source'] = source
        if isinstance(custom_details, dict):
            event['payload']['custom_details'] = custom_details
        if links:
            event['links'] = links
        self.send_change_event(**event)

    def trigger(self, summary, source, dedup_key=None, severity='critical',
            payload=None, custom_details=None, images=None, links=None) -> str:
        """
        Send an alert-triggering event

        :param summary:
            Summary / brief description of what is wrong.
        :param source:
            A human-readable name identifying the system that is affected.
        :param dedup_key:
            The deduplication key; used for determining event uniqueness and
            associating actions with existing incidents.
        :param severity:
            Alert severity. Sets the ``payload.severity`` property.
        :param payload:
            Set the payload directly. Can be used in conjunction with other
            parameters that also set payload properties; these properties will
            be merged into the default payload, and any properties in this
            parameter will take precedence except with regard to
            ``custom_details``.
        :param custom_details:
            The ``payload.custom_details`` property of the payload. Will
            override the property set in the ``payload`` parameter if given.
        :param images:
            Set the ``images`` property of the event.
        :param links:
            Set the ``links`` property of the event.
        :type action: str
        :type custom_details: dict
        :type dedup_key: str
        :type images: list
        :type links: list
        :type payload: dict
        :type severity: str
        :type source: str
        :type summary: str
        :returns:
            The deduplication key of the incident, if any.
        """
        for local in ('payload', 'custom_details'):
            local_var = locals()[local]
            if not (local_var is None or type(local_var) is dict):
                raise ValueError(local+" must be a dict")
        event = {'payload': {'summary':summary, 'source':source,
            'severity':severity}}
        if type(payload) is dict:
            event['payload'].update(payload)
        if type(custom_details) is dict:
            details = event.setdefault('payload', {}).get('custom_details', {})
            details.update(custom_details)
            event['payload']['custom_details'] = details
        if images:
            event['images'] = images
        if links:
            event['links'] = links
        return self.send_event('trigger', dedup_key=dedup_key, **event)


from typing import Iterator, List, Optional
import uuid

from . api_client import ApiClient
from . auth_method import AuthMethod
from . common import successful_response, try_decoding
from . rest_api_v2_base_client import (
    OAuthTokenAuthMethod,
    TokenAuthMethod
)

class ScimApiClient(ApiClient):
    """
    Client class for the PagerDuty SCIM API.

    This class features a method :attr:`list_users` that provides an interface for
    retrieving all users that match a given filter.

    Other endpoints of the PagerDuty SCIM API can be accessed through the standard
    methods named after the HTTP methods.

    Usage example:

    .. code-block:: python

        # Import and use OAuthTokenAuthMethod instead of TokenAuthMethod to use an
        # application OAuth token:
        from pagerduty import (
            ScimApiClient,
            TokenAuthMethod
        )

        # Instantiate:
        client = ScimApiClient(TokenAuthMethod(API_KEY))

        scim_users = client.list_users()

        create_users_response = client.post(
            '/Users',
            json = {
                ...
            }
        )
        if create_users_response.status == 201:
            print("User successfully created")

        scim_user_dict = create_users_response.json()

    """

    permitted_methods = ('DELETE', 'GET', 'PATCH', 'POST', 'PUT')

    url = 'https://api.pagerduty.com/scim/v2'

    def list_users(self, fltr: Optional[str] = None, start_index: int = 1,
            page_size: int = 100) -> List[dict]:
        """
        List all users using SCIM API with automatic pagination.

        :param fltr:
            Optional SCIM filter expression to limit results
        :param start_index:
            The 1-based index of the first result to return (SCIM standard)
        :param page_size:
            Number of results per page (default 100)
        :returns:
            List of all user entries from the SCIM Users endpoint
        """
        all_users = []
        current_start_index = start_index

        while True:
            params = {
                'startIndex': current_start_index,
                'count': page_size
            }

            if fltr:
                params['filter'] = fltr

            response = successful_response(
                self.get('/Users', params=params),
                context='SCIM list users pagination'
            )

            body = try_decoding(response)

            # Extract users from the SCIM response
            users = body.get('Resources', [])
            all_users.extend(users)

            # Check if there are more results
            total_results = body.get('totalResults', 0)
            items_per_page = body.get('itemsPerPage', len(users))

            # If no results are left, break:
            next_start_index = current_start_index + items_per_page - 1
            if next_start_index >= total_results or len(users) == 0:
                break

            # Move to next page
            current_start_index += items_per_page

        return all_users



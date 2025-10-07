from typing import Iterator, List, Optional
import uuid

from . api_client import ApiClient
from . auth_method import AuthMethod
from . common import successful_response, try_decoding
from . errors import HttpServerError
from . rest_api_v2_base_client import (
    OAuthTokenAuthMethod,
    TokenAuthMethod
)

class ScimApiClient(ApiClient):
    """
    Client class for the PagerDuty SCIM API.

    Usage example:

    .. code-block:: python

        # Import and use OAuthTokenAuthMethod instead of TokenAuthMethod to use an
        # application OAuth token:
        from pagerduty import (
            ScimApiClient,
            TokenAuthMethod
        )

        # Instantiate:
        auth_method = TokenAuthMethod(API_KEY)
        client = ScimApiClient(auth_method)

    """

    url = 'https://api.pagerduty.com/scim/v2'

    def list_users(self, start_index: int = 1, count: int = 100,
                   filter: Optional[str] = None) -> List[dict]:
        """
        List all users using SCIM API with automatic pagination.

        :param start_index:
            The 1-based index of the first result to return (SCIM standard)
        :param count:
            Number of results per page (default 100)
        :param filter:
            Optional SCIM filter expression to limit results
        :returns:
            List of all user entries from the SCIM Users endpoint
        """
        all_users = []
        current_start_index = start_index

        while True:
            params = {
                'startIndex': current_start_index,
                'count': count
            }

            if filter:
                params['filter'] = filter

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

            # If we've retrieved all results, break
            if current_start_index + items_per_page - 1 >= total_results:
                break

            # Move to next page
            current_start_index += items_per_page

        return all_users



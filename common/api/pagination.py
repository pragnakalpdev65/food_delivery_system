"""
Standard Pagination for LetsCall.AI API.

This module provides a consistent pagination format across all API endpoints.
The format is designed to be easy to understand and use in frontend applications.

Response Format:
    {
        "meta": {
            "page": 1,
            "pages": 5,
            "count": 100
        },
        "data": [...]
    }

Usage:
    The pagination class is set globally in settings.py, so it's automatically
    applied to all viewsets that return lists.

    Clients can customize page size:
        GET /api/v1/users/?page=2&page_size=50
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination class with consistent response format.

    Attributes:
        page_size: Default number of items per page (20)
        page_size_query_param: Query parameter to customize page size
        max_page_size: Maximum allowed page size (100)
    """

    # Default items per page
    page_size = 20

    # Allow clients to set page size via ?page_size=X
    page_size_query_param = "page_size"

    # Maximum items per page (prevent performance issues)
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Return paginated response with meta information.

        Args:
            data: Serialized list of items

        Returns:
            Response with meta and data keys
        """
        return Response(
            {
                "meta": {
                    "page": self.page.number,
                    "pages": self.page.paginator.num_pages,
                    "count": self.page.paginator.count,
                },
                "data": data,
            }
        )

"""
Pagination classes for Kirokiro.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination class with configurable page size.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Return enriched pagination metadata with page numbers."""
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,
                "pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


class LargePagination(PageNumberPagination):
    """
    Pagination class for large datasets.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class SmallPagination(PageNumberPagination):
    """
    Pagination class for small datasets.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

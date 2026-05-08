from rest_framework import pagination
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class StandardResultsSetPagination(pagination.PageNumberPagination):
    """
    Standard pagination for API views
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class LargeResultsSetPagination(pagination.PageNumberPagination):
    """
    Larger pagination for endpoints that need more data
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsSetPagination(pagination.PageNumberPagination):
    """
    Smaller pagination for real-time endpoints
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

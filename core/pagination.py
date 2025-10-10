import os
from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    page_size = int(os.getenv('PAGE_SIZE', '10'))
    page_size_query_param = 'page_size'
    max_page_size = int(os.getenv('PAGE_SIZE_MAX', '100'))



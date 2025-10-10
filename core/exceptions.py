from typing import Any, Optional
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Optional[Response]:
    response = exception_handler(exc, context)
    if response is None:
        return Response({'error': {'type': exc.__class__.__name__, 'detail': str(exc)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    detail = response.data
    if isinstance(detail, (list, str)):
        detail = {'detail': detail}
    formatted = {
        'error': {
            'status_code': response.status_code,
            'detail': detail,
        }
    }
    response.data = formatted
    return response



"""
Standardized API response utilities for consistent frontend consumption.
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message=None, meta=None, status_code=status.HTTP_200_OK):
    """
    Return standardized success response.
    Frontend can reliably expect { success, data, message, meta } structure.
    """
    response_data = {
        "success": True,
        "data": data,
        "message": message,
        "meta": meta or {},
    }
    return Response(response_data, status=status_code)


def error_response(message, code=None, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Return standardized error response.
    Ensures all errors follow predictable shape for Vue error handling.
    """
    response_data = {
        "success": False,
        "error": {
            "message": message,
            "code": code or "error",
            "details": details or {},
        },
    }
    return Response(response_data, status=status_code)

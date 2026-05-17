"""
Custom exception handler for DRF.
"""
import logging

from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    DRF exception handler producing standardized error envelopes.

    Args:
        exc: The raised exception instance.
        context: DRF view context dict.

    Returns:
        Response with structured {"error": {...}} payload or None.
    """
    # Log the exception
    logger.error(f"Exception occurred: {exc}", exc_info=True)

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response data
        if isinstance(exc, ValidationError):
            response.data = {
                "error": {
                    "code": "validation_error",
                    "message": "Validation failed",
                    "details": response.data,
                }
            }
        elif isinstance(exc, NotAuthenticated):
            response.data = {
                "error": {
                    "code": "not_authenticated",
                    "message": "Authentication credentials were not provided.",
                }
            }
        elif isinstance(exc, AuthenticationFailed):
            response.data = {
                "error": {
                    "code": "authentication_failed",
                    "message": "Authentication failed.",
                }
            }
        elif isinstance(exc, PermissionDenied):
            response.data = {
                "error": {
                    "code": "permission_denied",
                    "message": "You do not have permission to perform this action.",
                }
            }
        elif isinstance(exc, APIException):
            response.data = {
                "error": {
                    "code": "api_error",
                    "message": str(exc.detail),
                }
            }
    else:
        # Handle unexpected errors (500)
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            },
            status=500,
        )

    return response

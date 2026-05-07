import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def standardized_exception_handler(exc, context):
    """
    Custom exception handler that returns a standardized JSON format.

    Structure:
    {
        "status": "error",
        "code": "error_code",  # Machine readable
        "message": "Human readable message",
        "errors": { ... }      # Only for 400 Validation Errors
    }
    """

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # 1. Handle Unhandled Exceptions (500)
    # If response is None, it means DRF didn't catch it (e.g. key error, type error)
    if response is None:
        if isinstance(exc, (Http404, PermissionDenied)):
            # Let Django handle 404/403 or transform them manually if needed
            # For pure APIs, better to transform them
            pass

        # Log the critical error
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)

        return Response(
            {
                "status": "error",
                "code": "server_error",
                "message": "A server error occurred.",
            },
            status=500,
        )

    # 2. Format DRF Exceptions (400, 401, 403, 404, 429)
    # We transform the data into our standard structure
    original_data = response.data
    status_code = response.status_code

    # Defaults
    message = getattr(exc, "default_detail", "An error occurred.")
    code = getattr(exc, "default_code", "error")

    # If response data has 'detail' key, use it as the message
    if isinstance(original_data, dict) and "detail" in original_data:
        message = original_data["detail"]
        # If detail object has a code (e.g. PermissionDenied)
        if hasattr(message, "code"):
            code = message.code

    formatted_data = {
        "status": "error",
        "code": code,
        "message": str(message),  # Ensure it's a string
    }

    # Special Handling for 400 Validation Errors
    # Only override message for ValidationErrors, allowing other 400s (ParseError) to show custom message
    if status_code == 400 and isinstance(exc, ValidationError):
        formatted_data["code"] = "validation_error"
        formatted_data["message"] = "Validation failed."
        formatted_data["errors"] = original_data

    # Special Handling for 404 (if not custom detail)
    elif status_code == 404 and message == "Not found.":
        formatted_data["code"] = "not_found"
        # Convert standard DRF 404 message to our code, but keep custom messages

    # Override response data
    response.data = formatted_data

    return response

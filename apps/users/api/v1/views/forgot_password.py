from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.constants.messages import AuthMessages
from apps.users.api.v1.serializers.forgot_password import (
    ResetPasswordRequestSerializer,
    ResetPasswordConfirmSerializer
)
from django.contrib.auth import get_user_model
from rest_framework.throttling import ScopedRateThrottle

User = get_user_model()


class ResetPasswordRequestView(APIView):
    """
    API endpoint to request a password reset email.

        This endpoint allows users to request a password reset by submitting
        their registered email address. If the email exists in the system,
        a password reset email containing a signed token is sent.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "reset_password"

    def post(self, request):
        """Handle password reset email request."""

        # Initialize serializer with request data
        serializer = ResetPasswordRequestSerializer(data=request.data)

        # Validate email and check if user exists
        serializer.is_valid(raise_exception=True)

        # Send password reset email
        serializer.save()

        # Return success response
        return Response(
            {"message": AuthMessages.EMAIL_SENT},
            status=status.HTTP_200_OK
        )


class ResetPasswordConfirmView(APIView):
    """
    API endpoint to confirm password reset.

        This endpoint completes the password reset process using a valid
        reset token. The user must provide a new password and confirm it.
        If MFA is enabled, an MFA code must also be provided.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle password reset confirmation."""

        # Initialize serializer with request data
        serializer = ResetPasswordConfirmSerializer(data=request.data)

        # Validate token, password, and MFA if required
        serializer.is_valid(raise_exception=True)

        # Save the new password and blacklist existing tokens
        serializer.save()

        # Return success response
        return Response(
            {
                "message": AuthMessages.PASSWORD_RESET_SUCCESS
            },
            status=status.HTTP_200_OK,
        )

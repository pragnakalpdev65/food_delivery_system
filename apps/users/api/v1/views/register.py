from apps.users.api.v1.serializers.register import UserRegistrationSerializer, VerifyEmailSerializer, ResendVerificationSerializer
import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from apps.users.models import CustomUser
from apps.users.services.email_services import AuthEmailService
from apps.core.constants.messages import AuthMessages
from drf_spectacular.utils import extend_schema, OpenApiExample

@extend_schema(
    description="Register a new user",
    examples=[
        OpenApiExample(
            "Register",
            value={
                "email": "user@test.com",
                "username": "user",
                "password": "StrongPass123!",
                "user_type": "customer"
            }
        )
    ]
)
class UserRegistrationView(APIView):
    """
    API view responsible for user registration.

    Responsibilities:
    - Accept user registration data
    - Validate input using serializer
    - Create new user record
    - Send verification email
    - Return success response

    This endpoint is public and does not require authentication.
    """

    queryset = CustomUser.objects.all()
    permission_classes = []  # Public endpoint — any user can access

    def post(self, request):
        """
        Register a new user and send verification email.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuthEmailService().send_token_email(
                                user=user,
                                salt="email-verification",
                                url_name="verify-email",
                                subject="Verify your email - LetsCallAI",
                                template_name="verification",
                                context_key="verification_url",
                            ) # Send email verification link via service layer

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class VerifyEmailView(APIView):
    """
    API endpoint for verifying a user's email address.

    Workflow:
    - Accepts signed verification token via query params
    - Validates token integrity + expiration
    - Marks user as verified if valid
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Verify user's email using signed token.
        """
        serializer = VerifyEmailSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AuthMessages.VERIFIED_SUCCESS)
    
    
class ResendVerificationView(APIView):
    """
    API endpoint to resend verification email.

    Security considerations:
    - Public endpoint
    - Protected with rate limiting (throttling)
    - Prevents spam or brute-force email abuse
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "resend_email"

    def post(self, request):
        """
        Resend verification email to unverified user.
        """
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AuthMessages.EMAIL_SENT)
import logging

from rest_framework import serializers

from apps.users.models.user import CustomUser
from apps.users.services.auth_services import LoginService, LogoutService

logger = logging.getLogger(__name__)


class LoginSerializer(serializers.ModelSerializer):
    """Serializer responsible for handling user login."""

    username = serializers.CharField()
    password = serializers.CharField(min_length=8)

    class Meta:
        model = CustomUser
        # fields = ["email", "password","username"]
        fields = ["username", "password"]

    def validate(self, attrs):
        """
        Perform full login validation workflow.

        Steps:
        1. Validate required fields
        2. Check if account is locked
        3. Authenticate user credentials
        4. Verify email status
        5. Check MFA requirements
        6. Clear failed attempts if successful

        Returns:
            dict: Validated data including authenticated user
        """
        username = attrs.get("username")
        # username = attrs.get("username")
        password = attrs.get("password")
    
        # logger.info("Login attempt initiated", extra={"email": email})

        # # user = LoginService(email=email, username=username, password=password).login()
        user = LoginService(username=username, password=password).login()

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for handling user logout.

    This serializer:
    - Validates refresh token presence
    - Converts raw token string to RefreshToken object
    - Blacklists the token to invalidate future use
    - Handles invalid/expired tokens safely
    """

    refresh_token = serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ["refresh_token"]

    def validate(self, attrs):
        """
        Logout user by blacklisting the provided refresh token.

        Raises:
            AuthenticationFailed:
                - If token is missing
                - If token is invalid, expired, or malformed

        Returns:
            dict: Validated data
        """
        logger.info("Logout attempt.")
        token = attrs.get("refresh_token")
        LogoutService(token=token).logout()
        return attrs

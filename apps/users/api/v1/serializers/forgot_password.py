import logging

from rest_framework import serializers
from apps.core.constants.messages import AuthMessages
from apps.users.services.email_services import AuthEmailService
from apps.core.constants.error_codes import ErrorCodes
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


User = get_user_model()
logger = logging.getLogger(__name__)


class ResetPasswordRequestSerializer(serializers.Serializer):
    """ Serializer to handle password reset email requests."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate that the provided email belongs to an existing user."""

        logger.debug(f"Password reset requested for email={value}")

        user = User.objects.filter(email=value).first()

        if not user:
            logger.warning(f"Password reset requested for non-existent email={value}")
            raise serializers.ValidationError(
                AuthMessages.USER_NOT_FOUND, code=ErrorCodes.USER_NOT_FOUND
            )

        logger.info(f"Password reset request validated for user_id={user.id}")
        self.user = user
        return value

    def save(self, **kwargs):
        """Trigger the password reset email process."""

        logger.info(
            "Sending password reset email",
            extra={"user_id": self.user.id}
        )

        AuthEmailService().send_token_email(
                                user=self.user,
                                salt="reset-password",
                                url_name="reset_password_confirm",
                                subject="Reset your password - LetsCallAI",
                                template_name="reset_password",
                                context_key="reset_password_url",
                            )

        logger.info(
            "Password reset email sent",
            extra={"user_id": self.user.id}
        )

        return self.user


class ResetPasswordConfirmSerializer(serializers.Serializer):
    """Serializer to confirm and complete the password reset process."""

    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_token(self, value):
        """Validate and decode the password reset token."""

        logger.debug("Validating reset password token")

        try:
            self.data_payload = signing.loads(
                value, salt="reset-password", max_age=60 * 30
            )

            logger.debug("Token successfully decoded")

        except SignatureExpired:
            logger.warning("Password reset token expired")
            raise serializers.ValidationError(
                AuthMessages.TOKEN_EXPIRED,
                code=ErrorCodes.INVALID_TOKEN,
            )

        except BadSignature:
            logger.warning("Invalid password reset token signature")
            raise serializers.ValidationError(
                AuthMessages.INVALID_TOKEN,
                code=ErrorCodes.INVALID_TOKEN,
            )

        return value

    def validate_new_password(self, value):
        """Validate password strength using Django's password validators."""

        logger.debug("Validating new password")

        try:
            validate_password(value)
        except Exception as e:
            logger.warning("Password validation failed")
            raise serializers.ValidationError(
                str(e),
                code=ErrorCodes.INVALID_PASSWORD,
            )

        logger.debug("New password validated successfully")
        return value

    def validate(self, attrs):
        """Perform cross-field validation."""

        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        if new_password != confirm_password:
            logger.warning("Password confirmation mismatch during reset")
            raise serializers.ValidationError(
                AuthMessages.CONFIRM_PASSWORD,
                code=ErrorCodes.INVALID_PASSWORD,
            )

        user_id = self.data_payload.get("user_id")

        logger.debug(f"Fetching user for password reset user_id={user_id}")

        user = User.objects.filter(id=user_id).first()

        if not user:
            logger.error(f"User not found during password reset user_id={user_id}")
            raise serializers.ValidationError(
                AuthMessages.USER_NOT_FOUND,
                code=ErrorCodes.USER_NOT_FOUND,
            )
            
        try:
            validate_password(new_password, user=user)
        except Exception as e:
            logger.warning("Password validation failed during context check")
            raise serializers.ValidationError(
                str(e),
                code=ErrorCodes.INVALID_PASSWORD,
            )            

        self.user = user
        return attrs

    def save(self, **kwargs):
        """Complete the password reset process."""

        new_password = self.validated_data["new_password"]
        user = self.user

        logger.info(
            "Password reset attempt",
            extra={"user_id": user.id},
        )

        user.set_password(new_password)
        user.save(update_fields=["password"])

        logger.debug(
            "Password updated successfully",
            extra={"user_id": user.id},
        )

        # Blacklist all tokens
        tokens = OutstandingToken.objects.filter(user=user)

        logger.debug(
            f"Blacklisting {tokens.count()} tokens for user_id={user.id}"
        )

        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        logger.info(
            "Password reset successful",
            extra={"user_id": user.id},
        )

        return user

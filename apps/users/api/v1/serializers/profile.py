import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.users.models.user import CustomUser
from apps.users.models.profile import CustomerProfile, Address, DriverProfile

from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages
from apps.core.constants.cache_keys import CacheKey
from apps.users.services.email_services import AuthEmailService
from django.core import signing
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for Address model.

    Handles representation of user addresses including:
    - pin code
    - label (e.g., Home, Work)
    - full address
    - default flag
    """

    class Meta:
        model = Address
        fields = ["id", "pin_code", "label", "address", "is_default"]      

class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomerProfile model.

    Includes nested read-only addresses.
    Used for retrieving customer profile details.
    """

    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "user",
            "avatar",
            "default_address",
            "total_orders",
            "loyalty_points",
            "addresses",
        ]

class DriverProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for DriverProfile model.

    Used for retrieving driver profile details including:
    vehicle info, availability, and performance metrics.
    """

    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "avatar",
            "vehicle_type",
            "vehicle_number",
            "license_number",
            "is_available",
            "total_deliveries",
            "average_rating",
        ]

class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating CustomerProfile.

    Supports:
    - Updating avatar and default address
    - Replacing all addresses (if provided)

    Note:
    Existing addresses are deleted and replaced with new ones.
    """

    addresses = AddressSerializer(many=True, required=False)

    class Meta:
        model = CustomerProfile
        fields = ["avatar", "default_address", "addresses"]
        
        
    def update(self, instance, validated_data):
        addresses_data = validated_data.pop("addresses", None)
        default_address_id = validated_data.get("default_address", None)

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle addresses (optional)
        if addresses_data is not None:
            # instance.addresses.all().delete()

            for addr in addresses_data:
                Address.objects.create(customer=instance, **addr)

        # Sync default address
        if default_address_id:
            Address.objects.filter(customer=instance).update(is_default=False)

            Address.objects.filter(
                id=default_address_id.id,
                customer=instance
            ).update(is_default=True)

        return instance

class DriverProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating DriverProfile.

    Allows updating:
    - avatar
    - vehicle details
    - license information
    """
    addresses = AddressSerializer(many=True, required=False)

    class Meta:
        model = DriverProfile
        fields = ["avatar", "vehicle_type", "vehicle_number", "license_number"]

    def update(self, instance, validated_data):
        """
        Update driver profile instance.
        Only updates provided fields.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
        
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for handling password change requests.

    Fields:
    - current_password: User's existing password (for verification)
    - new_password: New password to be set (validated against Django password rules)
    """

    current_password = serializers.CharField(
        write_only=True
    )  # Hidden in responses for security
    new_password = serializers.CharField(
        write_only=True, min_length=8
    )  # Enforced minimum length + Django validators
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User

    def validate_new_password(self, value):
        """Apply Django's password validation rules."""
        try:
            # Initial validation without user context
            # Full validation with user context happens in validate() method
            validate_password(value)
        except ValidationError:
            raise serializers.ValidationError(
                AuthMessages.INVALID_PASSWORD, code=ErrorCodes.INVALID_PASSWORD
            )
        return value

    def validate(self, attrs):
        user = self.context["user"]
        current_password = attrs.get("current_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # Verify current password
        if not user.check_password(current_password):
            raise serializers.ValidationError(
                AuthMessages.CURRENT_PASSWORD,
                code=ErrorCodes.INVALID_PASSWORD,
            )

        # Check new password != current password
        if current_password == new_password:
            raise serializers.ValidationError(
                AuthMessages.NEW_PASSWORD,
                code=ErrorCodes.INVALID_PASSWORD,
            )
        # Check confirm password matches
        if new_password != confirm_password:
            raise serializers.ValidationError(
                AuthMessages.CONFIRM_PASSWORD,
                code=ErrorCodes.INVALID_PASSWORD,
            )

        return attrs

    def save(self, **kwargs):

        user = self.context["user"]
        new_password = self.validated_data["new_password"]

        logger.info("Password change attempt")
        self.validate_new_password(new_password)
        user.set_password(new_password)
        user.save()

        # Blacklist all tokens
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)

        logger.info(f"Password changed for user {user.id}")

        return user
       
class UpdateEmailSerializer(serializers.Serializer):
    """
    Initiates email change workflow.

    Flow:
        1. Validate password
        2. Check email uniqueness
        3. Send verification emails
        4. Store request in cache
    """

    current_password = serializers.CharField(write_only=True)
    new_email = serializers.EmailField()

    def validate_new_email(self, new_email):
        """
        Ensure email is not already registered.
        """
        logger.debug("Checking email availability", extra={"email": new_email})

        if User.objects.filter(email=new_email).exists():
            logger.warning("Email already exists", extra={"email": new_email})
            raise serializers.ValidationError(
                AuthMessages.EMAIL_ALREADY_EXISTS,
                code=ErrorCodes.EMAIL_EXISTS
            )

        return new_email

    def validate(self, attrs):
        """
        Validate user's current password.
        """
        user = self.context["user"]
        logger.debug("Validating current password", extra={"user_id": user.id})

        if not user.check_password(attrs.get("current_password")):
            logger.warning("Invalid password attempt", extra={"user_id": user.id})
            raise serializers.ValidationError(
                AuthMessages.CURRENT_PASSWORD,
                code=ErrorCodes.INVALID_PASSWORD,
            )

        return attrs

    def save(self, **kwargs):
        """
        Send verification emails and store request in cache.
        """
        user = self.context["user"]
        new_email = self.validated_data["new_email"]

        logger.info(
            "Initiating email change",
            extra={"user_id": user.id, "new_email": new_email}
        )

        # Send emails
        AuthEmailService().send_token_email(
            user=user,
            salt="current-email",
            url_name="current-email-confirm",
            subject="Confirm your email - LetsCallAI",
            template_name="current_email",
            context_key="authorization_url",
        )

        AuthEmailService().send_token_email(
            user=user,
            salt="new-email",
            url_name="confirm-email-change",
            subject="Confirm your new email - LetsCallAI",
            template_name="new_email",
            context_key="verification_url",
            to_email=new_email,
        )

        change_key = CacheKey.EMAIL_CHANGE % user.email
        cache.set(change_key, {
            "new_email": new_email,
            "old_confirmed": False,
            "new_confirmed": False
        }, timeout=60 * 60 * 24)

        logger.info("Email change request cached", extra={"user_id": user.id})

        return user

class CurrentEmailConfirmSerializer(serializers.Serializer):
    """
    Confirms user's old email using token validation.
    """

    old_token = serializers.CharField()

    def validate_old_token(self, value):
        """
        Validate old email token and prevent reuse.
        """
        logger.debug("Validating old email token")

        try:
            self.data_payload = signing.loads(
                value, salt="current-email", max_age=60 * 60 * 24
            )
        except SignatureExpired:
            logger.warning("Old token expired")
            raise serializers.ValidationError(
                AuthMessages.TOKEN_EXPIRED,
                code=ErrorCodes.INVALID_TOKEN
            )
        except BadSignature:
            logger.error("Invalid old token")
            raise serializers.ValidationError(
                AuthMessages.INVALID_TOKEN,
                code=ErrorCodes.INVALID_TOKEN
            )

        if cache.get(CacheKey.OLD_TOKEN % value):
            logger.warning("Old token reuse attempt")
            raise serializers.ValidationError(
                AuthMessages.TOKEN_EXPIRED,
                code=ErrorCodes.INVALID_TOKEN
            )

        return value

    def save(self, **kwargs):
        """
        Mark old email as confirmed.
        """
        user = self.context["user"]
        old_token = self.validated_data["old_token"]
        logger.info("Old email confirmed", extra={"user_id": user.id})

        cache.set(CacheKey.OLD_TOKEN % old_token, {"is_used": True}, timeout=60)
        mail_key = CacheKey.EMAIL_CHANGE % user.email
        data = cache.get(mail_key)

        if not data:
            logger.error("Email change request expired (old confirm)")
            raise serializers.ValidationError(
                AuthMessages.REQUEST_EXPIRED,
                code=ErrorCodes.REQUEST_EXPIRED)

        data["old_confirmed"] = True
        cache.set(mail_key, data, timeout=60 * 60 * 24)

        return user

class ConfirmEmailChangeSerializer(serializers.Serializer):
    """
    Finalizes email change after both confirmations.
    """

    new_token = serializers.CharField()

    def validate_new_token(self, value):
        """
        Validate new email token and prevent reuse.
        """
        logger.debug("Validating new email token")
 
        try:
            self.data_payload = signing.loads(
                value, salt="new-email", max_age=60 * 60 * 24
            )
        except SignatureExpired:
            logger.warning("New token expired")
            raise serializers.ValidationError(
                AuthMessages.TOKEN_EXPIRED,
                code=ErrorCodes.INVALID_TOKEN
            )
        except BadSignature:
            logger.error("Invalid new token")
            raise serializers.ValidationError(
                AuthMessages.INVALID_TOKEN,
                code=ErrorCodes.INVALID_TOKEN
            )

        if cache.get(CacheKey.NEW_TOKEN % value):
            logger.warning("New token reuse attempt")
            raise serializers.ValidationError(
                AuthMessages.TOKEN_EXPIRED,
                code=ErrorCodes.INVALID_TOKEN
            )

        return value

    def save(self, **kwargs):
        """
        Complete email update and invalidate existing sessions.
        """
        old_mail_user = self.context["user"]
        old_email = old_mail_user.email

        new_email = self.data_payload.get("email")
        new_token = self.validated_data["new_token"]
        logger.info("Completing email change", extra={"new_email": new_email})
        cache.set(CacheKey.NEW_TOKEN % new_token, {"is_used": True}, timeout=60)
        mail_key = CacheKey.EMAIL_CHANGE % old_email
        data = cache.get(mail_key)

        if not data:
            logger.error("Email change request expired (final step)")
            raise serializers.ValidationError(
                AuthMessages.REQUEST_EXPIRED,
                code=ErrorCodes.REQUEST_EXPIRED)

        if not data["old_confirmed"]:
            logger.warning("Old email not confirmed before new email")
            raise serializers.ValidationError("First confirm change from your old mail")

        data["new_confirmed"] = True
        cache.set(mail_key, data, timeout=60 * 60 * 24)

        if data["old_confirmed"] and data["new_confirmed"]:
            try:
                user = User.objects.get(email=old_email)
                user.email = new_email
                user.is_verified = False
                user.save(update_fields=["email", "is_verified"])
                logger.info("Email updated successfully", extra={"user_id": user.id})

                AuthEmailService().send_token_email(
                    user=user,
                    salt="email-verification",
                    url_name="verify-email",
                    subject="Verify your email - LetsCallAI",
                    template_name="verification",
                    context_key="verification_url",
                )

                tokens = OutstandingToken.objects.filter(user=user)
                for token in tokens:
                    BlacklistedToken.objects.get_or_create(token=token)
                logger.info("Tokens blacklisted after email change", extra={"user_id": user.id})

            except User.DoesNotExist:
                logger.error("User not found during email update")
                raise serializers.ValidationError(
                    AuthMessages.USER_NOT_FOUND,
                    code=ErrorCodes.USER_NOT_FOUND
                )

        cache.delete(mail_key)
        logger.debug("Cache cleared after email change")

        return user

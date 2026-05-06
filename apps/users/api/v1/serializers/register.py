import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from rest_framework import serializers

from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages
from apps.users.services.email_services import AuthEmailService

logger = logging.getLogger(__name__)
User = get_user_model()
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer responsible for handling user registration.

    This serializer performs the following tasks:
    - Accepts user registration data
    - Ensures the email address is unique
    - Validates password strength using Django's password validators
    - Creates a new active user with a hashed password
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long.",
    )
    email = serializers.EmailField(help_text="Unique email address for the user.")
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    user_type = serializers.ChoiceField(
        choices=[
            ("customer", "Customer"),
            ("restaurant_owner", "Restaurant Owner"),
            ("delivery_driver", "Delivery Driver"),
        ]
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "username",
            "first_name",
            "last_name",
            "user_type",
            "phone_number",
        ]
        
    def validate_username(self,username):
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                AuthMessages.USERNAME_ALREADY_EXIST, code=ErrorCodes.USERNAME_ALREADY_EXIST
            )
            
        return username

    def validate_email(self, email):
        """
        Validate that the provided email is unique.

        Raises:
            ValidationError: If email already exists.
        """
        logger.debug("Validating email for registration", extra={"email": email})
        if User.objects.filter(email=email).exists():
            logger.warning(
                "Registration attempted with existing email",
                extra={"email": email, "reason": "email_exists"},
            )
            raise serializers.ValidationError(
                AuthMessages.EMAIL_ALREADY_EXISTS, code=ErrorCodes.EMAIL_EXISTS
            )
        return email

    def validate_password(self, value):
        """
        Validate password strength using Django validators.

        Raises:
            ValidationError: If password does not meet requirements.
        """
        logger.debug("Validating password strength")
        try:
            # validate_password(value)
            # Create a temporary user instance for context-aware validation
            # This allows checking against username/email without saving to DB
            temp_user = User(
                username=self.initial_data.get('username', ''),
                email=self.initial_data.get('email', '')
            )
            validate_password(value, user=temp_user)
        except Exception as e:
            logger.warning("Password validation failed", extra={"reason": str(e)})
            raise serializers.ValidationError(
                str(e), code=ErrorCodes.INVALID_PASSWORD
            ) from e
        return value

    def create(self, validated_data):
        """
        Create and return a new user instance.
        """
        email = validated_data.get("email")

        logger.info("Creating user account", extra={"email": email})
        user = User.objects.create_user(
            email=email,
            username=validated_data.get("username"),
            password=validated_data["password"],
            first_name=validated_data.get("first_name") or "",
            last_name=validated_data.get("last_name") or "",
            phone_number=validated_data.get("phone_number"),
            user_type=validated_data.get("user_type"),
            is_active=True,
        )
        logger.info(
            "User account created successfully",
            extra={"user_id": user.id, "email": email},
        )
        return user

class VerifyEmailSerializer(serializers.Serializer):
    """
    Serializer used for verifying user email addresses.

    Responsibilities:
    - Validate signed verification token
    - Check expiration
    - Activate user's verified status
    """

    token = serializers.CharField()

    def validate_token(self, value):
        """
        Validate signed email verification token.

        Raises:
            ValidationError: If token is expired or invalid.
        """
        logger.debug("Verifying email token")
        try:
            self.data_payload = signing.loads(
                value, salt="email-verification", max_age=60 * 60 * 24
            )
            logger.info(
                "Email verification token valid",
                extra={"user_id": self.data_payload.get("user_id")},
            )

        except SignatureExpired:
            logger.warning(
                "Email verification token expired", extra={"reason": "expired"}
            )
            raise serializers.ValidationError(
                AuthMessages.TOKEN_EXPIRED, code=ErrorCodes.INVALID_TOKEN
            ) from None

        except BadSignature:
            logger.error(
                "Invalid email verification token received",
                extra={"reason": "bad_signature"},
            )
            raise serializers.ValidationError(
                AuthMessages.INVALID_TOKEN, code=ErrorCodes.INVALID_TOKEN
            ) from None

        return value

    def save(self, **kwargs):
        """
        Verify user email and update verification status.

        Returns:
            User: Verified user instance.
        """
        user_id = self.data_payload["user_id"]
        logger.debug("Fetching user for email verification", extra={"user_id": user_id})

        try:
            user = User.objects.get(id=user_id)

        except User.DoesNotExist as err:

            logger.error(
                "User not found during email verification", extra={"user_id": user_id}
            )
            raise serializers.ValidationError(
                AuthMessages.USER_NOT_FOUND, code=ErrorCodes.USER_NOT_FOUND
            ) from err

        if user.is_verified:
            raise serializers.ValidationError(
                AuthMessages.ALREADY_VERIFIED, code=ErrorCodes.ALREADY_VERIFIED
            )
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        logger.info("User email verified successfully", extra={"user_id": user.id})

        return user

class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending email verification links.

    Responsibilities:
    - Validate email existence
    - Ensure account not already verified
    - Trigger verification email resend
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Validate email before resending verification email.

        Raises:
            ValidationError: If user not found or already verified.
        """
        logger.debug("Resend verification requested", extra={"email": value})
        user = User.objects.filter(email=value).first()

        if not user:
            raise serializers.ValidationError(
                AuthMessages.USER_NOT_FOUND, code=ErrorCodes.USER_NOT_FOUND
            )

        if user.is_verified:
            raise serializers.ValidationError(
                AuthMessages.ALREADY_VERIFIED, code=ErrorCodes.ALREADY_VERIFIED
            )

        self.user = user
        return value

    def save(self, **kwargs):
        """
        Send verification email to the user.

        Returns:
            User: User instance email was sent to.
        """
        logger.info(
            "Sending verification email",
            extra={"user_id": self.user.id, "email": self.user.email},
        )

        AuthEmailService().send_token_email(
                                user=self.user,
                                salt="email-verification",
                                url_name="verify-email",
                                subject="Verify your email - LetsCallAI",
                                template_name="verification",
                                context_key="verification_url",
                            )

        logger.info(
            "Verification email sent successfully",
            extra={"user_id": self.user.id, "email": self.user.email},
        )

        return self.user

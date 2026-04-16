import logging
import time

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q        

from apps.core.constants.cache_keys import CacheKey
from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages
from apps.users.models.user import CustomUser
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

# User= get_user_model()         

class LoginService:
    """Handles full login workflow."""

    def __init__(self, username, password):

        self.username = username
        self.password = password

    def login(self) -> CustomUser:
        # logger.info("Login attempt initiated", extra={"username": self.username})

        self.validate_required_fields()
        self.check_account_lock()

        user = self.authenticate_user()
        self.check_email_verification(user)

        self.clear_login_attempts()

        # logger.info("Login successful", extra={"username": self.email, "user_id": user.id})

        return user

    # ----------------------------
    # Validation Helpers
    # ----------------------------
    def validate_required_fields(self) -> None:
        """
        Ensure both email and password are provided.
        Raises:
            AuthenticationFailed: If credentials are missing.
        """
        if not self.username or not self.password:
            logger.warning("Login failed — missing credentials")
            raise AuthenticationFailed(
                AuthMessages.MISSING_CREDENTIALS,
                code=ErrorCodes.MISSING_CREDENTIALS,
            )
    

    def authenticate_user(self) -> CustomUser:
        """
        Authenticate user credentials.

        Raises:
            AuthenticationFailed: If credentials are invalid.
        """
        
        user = CustomUser.objects.filter(
            Q(username=self.username) | Q(email=self.username)
        ).first()
        
        if not user or not user.check_password(self.password):
            self.track_failed_attempt()
            raise AuthenticationFailed(
                AuthMessages.INVALID_CREDENTIALS,
                code=ErrorCodes.INVALID_CREDENTIALS,
            )

        return user
        # from django.contrib.auth import authenticate
        
        # user = authenticate(username=CustomUser.objects.filter(email=self.email).first().username, password=self.password)
        
        # user = MultiFieldBackend().authenticate(self.username, self.password)

        return user

    @staticmethod
    def check_email_verification(user: CustomUser) -> None:
        """
        Ensure the user's email address is verified.

        Raises:
            PermissionDenied: If email is not verified.
        """
        if not user.is_verified:
            logger.warning(
                "Login blocked — email not verified",
                extra={"email": user.email, "user_id": user.id},
            )
            raise PermissionDenied(
                AuthMessages.EMAIL_UNVERIFIED,
                code=ErrorCodes.EMAIL_UNVERIFIED,
            )

    def get_attempt_key(self) -> str:
        """
        Generate cache key for tracking failed login attempts.
        """
        return CacheKey.LOGIN_ATTEMPTS_PREFIX % self.username

    def get_lock_key(self) -> str:
        """
        Generate cache key for tracking account lock status.
        """
        return CacheKey.LOGIN_LOCK_PREFIX % self.username

    def check_account_lock(self) -> None:
        """
        Check if the user account is temporarily locked due to
        too many failed login attempts.

        Raises:
            PermissionDenied: If account is currently locked.
        """
        lock_key = self.get_lock_key()
        lock_time = cache.get(lock_key)

        if lock_time:
            elapsed = time.time() - lock_time
            remaining = settings.ACCOUNT_LOCKOUT_TIME - elapsed

            if remaining > 0:
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)

                logger.warning(
                    "Account locked",
                    extra={
                        "minutes": minutes,
                        "seconds": seconds,
                        "event": "account_lock",
                        "username": self.username,
                    },
                )

                raise PermissionDenied(
                    (AuthMessages.ACCOUNT_LOCKED_DURATION)
                    % {"minutes": minutes, "seconds": seconds},
                    code=ErrorCodes.LOCKED_ACCOUNT,
                )

    def track_failed_attempt(self) -> None:
        """
        Track failed login attempts using cache.

        If failed attempts exceed MAX_LOGIN_ATTEMPTS,
        the account will be temporarily locked.
        """
        attempt_key = self.get_attempt_key()
        lock_key = self.get_lock_key()

        failed_attempts = cache.get(attempt_key, 0) + 1

        cache.set(
            attempt_key,
            failed_attempts,
            timeout=settings.ACCOUNT_LOCKOUT_TIME,
        )

        logger.warning(
            "Invalid login attempt",
            extra={"username": self.username, "attempts": failed_attempts},
        )

        if failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            cache.set(
                lock_key,
                time.time(),
                timeout=settings.ACCOUNT_LOCKOUT_TIME,
            )

            logger.error(
                "Account locked due to max attempts",
                extra={"username": self.username, "attempts": failed_attempts},
            )

    def clear_login_attempts(self) -> None:
        """
        Clear cached login attempts and lock status
        after successful authentication.
        """
        cache.delete(self.get_attempt_key())
        cache.delete(self.get_lock_key())

    @staticmethod
    def generate_tokens_for_user(user):
        """Handles JWT token operations."""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class LogoutService:
    """Handles logout workflow."""

    def __init__(self, token):
        self.token = token

    def logout(self) -> None:
        logger.info("Logout attempt.")

        if not self.token:
            logger.warning("Logout failed — missing refresh token.")
            raise AuthenticationFailed(
                AuthMessages.REFRESH_TOKEN_REQUIRED,
                code=ErrorCodes.MISSING_TOKEN,
            )

        try:
            refresh_token = RefreshToken(self.token)
            refresh_token.blacklist()
            logger.info("Logout successful.")

        except (InvalidToken, TokenError) as err:
            logger.error("Logout failed — invalid token.", extra={"reason": str(err)})
            raise AuthenticationFailed(
                AuthMessages.INVALID_TOKEN,
                code=ErrorCodes.INVALID_TOKEN,
            ) from err

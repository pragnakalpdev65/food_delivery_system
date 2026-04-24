from django.utils.translation import gettext_lazy as _


class AuthMessages:
    """Centralized user-facing authentication and authorization messages."""

    # Required fields
    EMAIL_REQUIRED = _("Email is required.")
    PASSWORD_REQUIRED = _("Password is required.")
    MISSING_CREDENTIALS = _("Email and password required.")
    MFA_REQUIRED = _("MFA is required")

    # Authentication errors
    INVALID_CREDENTIALS = _("Invalid email or password.")
    ACCOUNT_LOCKED = _("Your account is locked.")
    ACCOUNT_LOCKED_DURATION = _(
        "Account locked for %(minutes)s minutes and %(seconds)s seconds."
    )

    # Account status
    USERNAME_ALREADY_EXIST = _("Username already taken")
    EMAIL_UNVERIFIED = _("Email not verified")
    EMAIL_ALREADY_EXISTS = _("An account with this email already exists.")
    USER_NOT_FOUND = _("User not found")
    ALREADY_VERIFIED = _("Account already verified")

    # Token-related errors
    TOKEN_EXPIRED = _("Token is expired")
    INVALID_TOKEN = _("Invalid token.")
    MISSING_TOKEN = _("Token is missing")
    REFRESH_TOKEN_REQUIRED = _("Refresh token is required")

    # Password validation
    INVALID_PASSWORD = _("Password is invalid.")
    CURRENT_PASSWORD = _("Current password is incorrect.")
    NEW_PASSWORD = _("New password must be different from current password.")
    CONFIRM_PASSWORD = _("New password and Current password does not match.")

    # Success messages
    LOGIN_SUCCESS = _("User Login successfully.")
    LOGOUT_SUCCESS = _("User logged out successfully.")
    PASSWORD_CHANGE_SUCCESS = _(
        "Password changed successfully.Please login again."
    )
    VERIFIED_SUCCESS = _("Email Verified successfully")
    EMAIL_SENT = _("Mail sent successfully")
    PASSWORD_RESET_SUCCESS = _("Password reset successfully")
    EMAIL_SENT_TO_UPDATED_ADDRESS = _("Verification emails sent to current and new address")
    EMAIL_UPDATED = _("Email updated successfully")

    # Profile
    AVATAR_VALIDATION =_("Avatar must be less than 5MB")
    CONFIRM_OLD_EMAIL = _("Changes in mail is confirmed by old email")
    REQUEST_EXPIRED = _("Request expired")
    CUSTOMER_NOT_FOUND = _("Customer profile not found")
    DRIVER_NOT_FOUND = _("Driver profile not found")
    ADDRESS_NOT_FOUND = _("Address profile not found")

    #restaurants
    
    ADD_MENU_PERMISSION_DENIED = _("Only Restaurant Owners can add menu items.")
    


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
    

    # order
    ALREADY_CANCELLED = _("Order is already cancelled")
    CAN_NOT_BE_CANCELLED = _("Order cannot be cancelled at this stage")
    CANCELLED_SUCCESS = _("Order cancelled successfully")
    UPDATE_ORDER = _("Order updated")
    INVALID_ORDER = _("Invalid order")
    DRIVER_REQUIRED = _( "driver_id is required")
    DRIVER_NOT_FOUND = _("Driver profile not found")
    ALREADY_ASSIGNED = _("Driver already assigned")
    MUST_BE_READY = _("Order must be READY before assigning driver")
    ASSIGN_SUCCESS = _("Driver assigned successfully")
    STATUS_REQUIRED = _("Status is required")
    INVALID_TRANSITION = _(
        "Invalid transition from %(current_status)s to %(new_status)s"
    )
    STATUS_UPDATE_SUCCESS = _("Order status updated successfully")
    REQUIRED_QUANTITY = _("Quantity must be greater than 0")
    CONTAIN_ONE_ITEM = _("Order must contain at least one item")
    ITEM_BELONGS_TO_ONE_RESTAURANT = ("All items must belong to the selected restaurant")
    MENU_ITEM_UNAVAILABLE = _(
        "'%(item_name)s' is currently unavailable"
    )
    MINIMUM_ORDER_NOT_MET = _(
        "Order total must meet the restaurant's minimum order of %(minimum_order)s"
    )
    
    #Review
    
    RATING_VALIDATION = _("Rating must be between 1 and 5")
    REVIEW_OWN_ORDER = _("You can only review your own order")
    REVIEW_DELIVERED_ORDER = _("Order must be delivered to review")
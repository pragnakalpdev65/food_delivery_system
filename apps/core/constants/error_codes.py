class ErrorCodes:

    # Authentication
    MISSING_CREDENTIALS = "missing_credentials"
    LOCKED_ACCOUNT = "locked_account"
    INVALID_CREDENTIALS = "invalid_credentials"
    EMAIL_UNVERIFIED = "email_unverified"
    MFA_REQUIRED = "mfa_required"
    MISSING_TOKEN = "missing_token"
    INVALID_TOKEN = "invalid_token"
    EMAIL_EXISTS = "email_already_exists"
    USER_NOT_FOUND = "user_not_found"
    ALREADY_VERIFIED = "already_verified"
    USERNAME_ALREADY_EXIST = "username_taken"
    INVALID_PASSWORD = "invalid_password"

    # Profile

    REQUEST_EXPIRED = "request_expired"
    NOT_FOUND = 404
    
    #order
    
    INVALID_TRANSITIONS = "invalid_transition" 
    MUST_BE_READY = "must_be_ready_state"
    ALREADY_ASSIGNED = "already_assigned"
    DRIVER_NOT_FOUND = "driver_profile_not_found"
    DRIVER_REQUIRED = "driver_required"
    CAN_NOT_BE_CANCELLED = "can_not_be_cancelled"


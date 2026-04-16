from django.urls import path
from .views.register import UserRegistrationView,VerifyEmailView, ResendVerificationView
from .views.login import LoginView, LogoutView
from .views.forgot_password import ResetPasswordRequestView, ResetPasswordConfirmView
from .views.profile import CustomerProfileView,AddressView,AddressDetailView,DriverProfileView,ChangePasswordView,UpdateEmailView,CurrentEmailConfirmView,ConfirmEmailChangeView


urlpatterns = [
        path("auth/register/", UserRegistrationView.as_view(), name="register"),
        path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
        path("auth/resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
        path("auth/login/", LoginView.as_view(), name="login"),
        path("auth/logout/", LogoutView.as_view(), name="logout"),
        path("auth/reset-request/", ResetPasswordRequestView.as_view(), name="reset_password_request"),
        path("auth/reset-confirm/", ResetPasswordConfirmView.as_view(), name="reset_password_confirm"),
        path("profile/customer/", CustomerProfileView.as_view(), name="customer-profile"),
        path("profile/customer/addresses/", AddressView.as_view(), name="address-list-create"),
        path("profile/customer/addresses/<uuid:pk>/", AddressDetailView.as_view(), name="address-detail"),
        path("profile/driver/", DriverProfileView.as_view(), name="driver-profile"),        
        path("profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
        path("profile/email/change-request/", UpdateEmailView.as_view(), name="email-change-request"),
        path("profile/email/current-confirm/", CurrentEmailConfirmView.as_view(), name="current-email-confirm"),
        path("profile/email/change-confirm/", ConfirmEmailChangeView.as_view(), name="confirm-email-change"),
    
]



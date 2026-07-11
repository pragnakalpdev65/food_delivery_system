from django.urls import path
from .views.register import UserRegistrationView,VerifyEmailView, ResendVerificationView
from rest_framework_simplejwt.views import TokenRefreshView
from .views.login import LoginView, LogoutView
from .views.forgot_password import ResetPasswordRequestView, ResetPasswordConfirmView
from .views.profile import CustomerProfileView,AddressView,AddressDetailView,DriverProfileView,ChangePasswordView,UpdateEmailView,CurrentEmailConfirmView,ConfirmEmailChangeView,RestaurantOwnerProfileView
from .views.drivers import DriverListView
from rest_framework.routers import DefaultRouter
from apps.users.api.v1.views.favorites import (
    FavoriteRestaurantViewSet,
    FavoriteMenuItemViewSet,
)
from apps.users.api.v1.views.order_stats import UserOrderStatsView

router = DefaultRouter()
router.register(
    r"favorites/restaurants",
    FavoriteRestaurantViewSet,
    basename="favorite-restaurants",
)
router.register(
    r"favorites/menu-items",
    FavoriteMenuItemViewSet,
    basename="favorite-menu-items",
)

urlpatterns = [
    path("auth/register/", UserRegistrationView.as_view(), name="register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/reset-request/", ResetPasswordRequestView.as_view(), name="reset_password_request"),
    path("auth/reset-confirm/", ResetPasswordConfirmView.as_view(), name="reset_password_confirm"),

    path("profile/customer/", CustomerProfileView.as_view(), name="customer-profile"),
    path("profile/customer/addresses/", AddressView.as_view(), name="address-list-create"),
    path("profile/customer/addresses/<uuid:pk>/", AddressDetailView.as_view(), name="address-detail"),
    path("profile/driver/", DriverProfileView.as_view(), name="driver-profile"),
    path("drivers/", DriverListView.as_view(), name="driver-list"),
    path("profile/restaurant-owner/",RestaurantOwnerProfileView.as_view(),name="restaurant-owner-profile",),      
    path("profile/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("profile/email/change-request/", UpdateEmailView.as_view(), name="email-change-request"),
    path("profile/email/current-confirm/", CurrentEmailConfirmView.as_view(), name="current-email-confirm"),
    path("profile/email/change-confirm/", ConfirmEmailChangeView.as_view(), name="confirm-email-change"),

    path("order-stats/", UserOrderStatsView.as_view(), name="order-stats"),
]

urlpatterns += router.urls
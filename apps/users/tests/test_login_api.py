import time

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def user():
    user = User.objects.create_user(
        email="test@example.com",
        password="securepass123!",
        username = "TestUser",
        first_name = "Test",
        last_name = "User",
        user_type = "customer",
        is_verified=True,
    )
    return user


# =========================================================
# Test Suite: Login API
# Purpose: Validate authentication, security checks, and lockout logic
# =========================================================
@pytest.mark.django_db
class TestLoginAPI:
    # Tests for login endpoint behavior and security scenarios

    def test_successful_user_login(self, api_client, user):
        """Login succeeds with valid credentials and verified email."""

        url = reverse("login")
        payload = {
            "username": "test@example.com",
            "password": "securepass123!",
        }

        response = api_client.post(url, payload, format="json")

        assert "refresh" in response.data
        assert "access" in response.data

        refresh = RefreshToken(
            response.data["refresh"]
        )  # Ensure token belongs to correct user

        assert refresh["user_id"] == str(user.id)
        assert response.status_code == status.HTTP_200_OK


    def test_missing_credentials(self, api_client):
        """Login should fail if email/password not provided."""

        url = reverse("login")
        payload = {}
        response = api_client.post(url, payload, format="json")
        assert response.data["username"][0] == "This field is required."
        assert response.data["password"][0] == "This field is required."


    def test_invalid_credentials(self, api_client, user):
        """Invalid credentials should return 401 without revealing details."""

        url = reverse("login")
        payload = {
            "username": "testuser3",  # intentionally wrong
            "password": "wrongPass123!",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 401
        assert response.data["detail"] == "Invalid email or password."

    def test_unverified_user_blocked(self, api_client):
        """Users with unverified email should not be allowed to login."""

        url = reverse("login")
        User.objects.create_user(
            email="test@example.com",
            password="securepass123!",
            username="Test User",
            first_name = "Test",
            last_name = "User",
            user_type = "customer",
            is_verified=False,
        )
        payload = {
            "username": "test@example.com",
            "password": "securepass123!",
        }
        response = api_client.post(url, payload, format="json")
        assert response.data["detail"] == "Email not verified"
        assert response.status_code == 403

    def test_account_lock_after_max_attempts(self, api_client, user):
        """Account should be locked after exceeding allowed login attempts."""

        url = reverse("login")
        payload = {
            "username": "test@example.com",
            "password": "wrongPass123!",
        }
        # Exceed allowed attempts
        for _ in range(settings.MAX_LOGIN_ATTEMPTS):
            response = api_client.post(url, payload, format="json")

        assert response.status_code == 401

        response = api_client.post(url, payload, format="json")
        
        assert response.status_code == 403
        assert "Account locked" in response.data["detail"]

    def test_locked_user_cannot_login(self, api_client, user):
        """If user is already locked, login should immediately fail."""

        url = reverse("login")
        lock_key = f"login_lock:{user.email}"
        cache.set(lock_key, time.time(), timeout=settings.ACCOUNT_LOCKOUT_TIME)
        payload = {
            "username": "test@example.com",
            "password": "securepass123!",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 403
        assert "Account locked" in response.data["detail"]


# =========================================================
# Test Suite: Logout API
# Purpose: Ensure refresh tokens are invalidated securely on logout
# =========================================================
@pytest.mark.django_db
class TestLogoutAPI:
    # Tests for logout endpoint including token invalidation logic
    def test_successful_logout(self, api_client, user):
        """Valid refresh token should be blacklisted and logout succeed."""

        url = reverse("logout")
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {"refresh_token": str(refresh)}
        # First logout attempt should succeed
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_205_RESET_CONTENT
        assert "User logged out successfully." in response.data

        # Reusing same token should fail because it is now blacklisted
        response = api_client.post(url, payload, format="json")
        assert "Invalid token." in response.data["detail"]

    def test_logout_without_token(self, api_client, user):
        """Logout should fail if refresh token is missing."""

        url = reverse("logout")
        refresh = RefreshToken.for_user(user)
        # Authenticate request
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = api_client.post(
            url, {}, format="json"
        )  # Send request without refresh token

        assert (
            response.data["refresh_token"][0] == "This field is required."
        )  # API should reject request due to missing token

    def test_logout_invalid_token(self, api_client, user):
        """Malformed or invalid tokens should be rejected."""

        url = reverse("logout")
        refresh = RefreshToken.for_user(user)
        # Authenticate request
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {"refresh_token": "invalidtoken"}  # intentionally malformed

        response = api_client.post(url, payload, format="json")
        # API should reject invalid token format
        assert "Invalid token." in response.data["detail"]

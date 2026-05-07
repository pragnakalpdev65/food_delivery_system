import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.core.signing import SignatureExpired
from django.template.loader import render_to_string
from django.urls import reverse

from apps.users.services.email_services import AuthEmailService
from common.services.email import BaseEmailService
from apps.users.api.v1.serializers.forgot_password import ResetPasswordConfirmSerializer
from apps.core.constants.messages import AuthMessages

# Get active User model (supports custom user model)
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
    )
    return user


@pytest.mark.django_db
class TestResetPasswordRequestAPI:

    def test_email_sent_on_reset_password_request(self, api_client, settings,user):

        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        url = reverse("reset_password_request")
        payload = {
            "email": user.email,
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.to == ["test@example.com"]
        assert "Reset your password - LetsCallAI" in email.subject

    def test_reset_password_url_generation(settings):
        """Ensure verification URL format is correct."""
        settings.SITE_BASE_URL = "https://example.com"
        user = User.objects.create(email="test@test.com")
        service = AuthEmailService()
        salt = "reset-password"
        token = service.generate_token(user,salt)
        expected = f"https://example.com/api/v1/users/auth/reset-request/?token={token}"

        reset_password_path = reverse("reset_password_request")
        reset_password_url = f"{settings.SITE_BASE_URL}{reset_password_path}?token={token}"
        assert reset_password_url == expected


    def test_user_not_found(self, api_client):
        """Ensure resend fails if user missing."""
        url = reverse("reset_password_request")
        response = api_client.post(url, {"email": "usermissing@test.com"})
        assert response.status_code == 400
        assert "User not found" in response.data["errors"]["email"][0]

@pytest.mark.django_db
class TestResetPasswordConfirmAPI:

    def test_invalid_token(self, api_client):
        """Ensure invalid token fails."""
        url = reverse("reset_password_confirm")
        response = api_client.post(url, {"token": "invalid token"})
        assert response.status_code == 400

        assert "Invalid token" in response.data["errors"]["token"][0]

    def test_expired_token(self, api_client):
        """Ensure expired token is rejected."""
        user = User.objects.create(email="test@test.com")
        token = signing.dumps({"user_id": str(user.id)}, salt="reset-password")

        # This ensures signing system treats token as expired
        with pytest.raises(SignatureExpired):
            signing.loads(token, salt="reset-password", max_age=0)

    def test_new_password_validations(self, api_client, user):
        """Should fail if new password does not meet validation rules."""

        api_client.force_authenticate(user=user)
        email_service = AuthEmailService()
        salt =  salt = "reset-password"
        token = email_service.generate_token(user,salt)

        # Same password used again
        payload = {
            "token" : token,
            "new_password": "sec4!",
            "confirm_password": "securepass1234!",
        }
        serializer = ResetPasswordConfirmSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False
        assert "new_password" in serializer.errors

    def test_confirm_password_same_as_new_password(self, api_client, user):
        """Should fail validation if confirm_password does not match new_password."""

        api_client.force_authenticate(user=user)
        email_service = AuthEmailService()
        salt = "reset-password"
        token = email_service.generate_token(user,salt)

        # Same password used again
        payload = {
            "token": token,
            "new_password": "securepass1234!",
            "confirm_password": "secure123!",
        }
        serializer = ResetPasswordConfirmSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False

        assert (
            "New password and Current password does not match."
            in serializer.errors["non_field_errors"][0])

   
   
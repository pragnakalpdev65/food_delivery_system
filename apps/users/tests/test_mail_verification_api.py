import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail, signing
from django.core.signing import SignatureExpired
from django.template.loader import render_to_string
from django.urls import reverse

from apps.users.services.email_services import AuthEmailService
from common.services.email import BaseEmailService

User = get_user_model()


# =========================================================
# Test Suite: Email Template Rendering
# Purpose: Ensure template variables render correctly
# =========================================================
@pytest.mark.django_db
class TestEmailTemplates:
    """Tests email template rendering."""

    def test_welcome_email_template_renders(self):
        """Ensure welcome template renders dynamic values."""
        context = {"user_name": "Test User", "app_name": "MyApp"}

        subject = render_to_string("email/verification.txt", context).strip()
        body = render_to_string("email/verification.txt", context)

        assert "Verify your email - Food Delivery" in subject
        assert "Verify your email - Food Delivery" in body
        assert "Food Delivery" in body


# =========================================================
# Test Suite: Registration Email Flow
# Purpose: Ensure email is sent after successful registration
# =========================================================
@pytest.mark.django_db
class TestRegistrationEmailFlow:
    """Tests registration email sending."""

    def test_email_sent_on_registration(self, api_client, settings):
        """Ensure registration triggers email."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        url = reverse("register")
        payload = {
            "email": "emailflow@example.com",
            "password": "StrongPass123!",
            "username":"TestUser",
            "first_name": "Test",
            "last_name": "User",
            "user_type":"customer",
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == 201
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.to == ["emailflow@example.com"]
        assert "verify your email" in email.subject.lower()


# =========================================================
# Unit Test: BaseEmailService.send_email()
# Purpose: Verify email sending logic works correctly
# =========================================================
@pytest.mark.django_db
def test_send_email_success(settings):
    """Ensure BaseEmailService sends email."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    BaseEmailService().send_email(
        "Test Subject", "unit@test.com", "verification", {"user_name": "Test"}
    )
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Test Subject"


# =========================================================
# Test Suite: Verification URL Generation
# Purpose: Ensure verification link format is correct
# =========================================================
class TestUrl:
    """Tests verification URL generation."""

    @pytest.mark.django_db
    def test_verification_url_generation(settings):
        """Ensure verification URL format is correct."""
        settings.SITE_BASE_URL = "https://example.com"
        user = User.objects.create(email="test@test.com")
        service = AuthEmailService()
        salt = "email-verification"
        token = service.generate_token(user,salt)
        expected = f"https://example.com/api/v1/users/auth/verify-email/?token={token}"

        verification_path = reverse("verify-email")
        verification_url = f"{settings.SITE_BASE_URL}{verification_path}?token={token}"
        assert verification_url == expected


# =========================================================
# Test Suite: Email Verification Flow
# Purpose: Validate verification endpoint behavior
# =========================================================
@pytest.mark.django_db
class TestEmailFlow:
    """Tests email verification endpoint."""

    def test_verify_email_success(self, api_client):
        """Ensure valid token verifies email."""
        user = User.objects.create(email="test@test.com", is_verified=False)
        email_service = AuthEmailService()
        salt = "email-verification"
        token = email_service.generate_token(user,salt)
        url = reverse("verify-email")
        response = api_client.get(url, {"token": token})

        user.refresh_from_db()
        assert response.status_code == 200
        assert user.is_verified is True

    def test_verify_email_invalid_token(self, api_client):
        """Ensure invalid token fails."""
        url = reverse("verify-email")
        response = api_client.get(url, {"token": "invalid token"})
        
        assert response.status_code == 400
        assert "Invalid token." in response.data["token"][0]

    def test_verify_email_expired_token(self, api_client):
        """Ensure expired token is rejected."""
        user = User.objects.create(email="test@test.com")
        token = signing.dumps({"user_id": str(user.id)}, salt="email-verification")

        # This ensures signing system treats token as expired
        with pytest.raises(SignatureExpired):
            signing.loads(token, salt="email-verification", max_age=0)


# =========================================================
# Test Suite: Resend Verification Email
# Purpose: Validate resend email endpoint logic
# =========================================================
@pytest.mark.django_db
class TestResendEmail:
    """Tests resend verification email endpoint."""

    def test_resend_email_success(self, api_client, settings):
        """Ensure resend works for unverified user."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        user = User.objects.create(email="test@test.com", is_verified=False)
        url = reverse("resend-verification")
        response = api_client.post(url, {"email": user.email}, format="json")

        assert response.status_code == 200
        assert len(mail.outbox) == 1

    def test_resend_email_user_not_found(self, api_client):
        """Ensure resend fails if user missing."""
        url = reverse("resend-verification")
        response = api_client.post(url, {"email": "usermissing@test.com"})
        
        print(response.data)
        assert response.status_code == 400
        assert "User not found" in response.data["email"][0]

    def test_resend_email_already_verified(self, api_client):
        """Ensure resend blocked for verified user."""
        user = User.objects.create(email="test@test.com", is_verified=True)
        url = reverse("resend-verification")
        response = api_client.post(url, {"email": user.email})

        assert response.status_code == 400
        assert "Account already verified" in response.data["email"][0]


# =========================================================
# Test Suite: Full Registration + Email Verification Flow
# This is an end-to-end integration test ensuring all layers
# work together correctly.
# =========================================================
@pytest.mark.django_db
class TestFullRegistration:
    """Tests full registration-to-verification flow."""

    def test_full_registration_verification_flow(self, api_client, settings):
        """Ensure full flow works end-to-end."""
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        # Step 1 — Registration endpoint
        url = reverse("register")
        payload = {
            "email": "emailflow@example.com",
            "password": "StrongPass123!",
            "username":"TestUser",
            "first_name": "Test",
            "last_name": "User",
            "user_type":"customer",
        }
        response = api_client.post(url, payload, format="json")

        assert response.status_code == 201

        # Step 2 — Verify that a verification email was sent
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        # Step 3 — Extract verification token from email body using regex
        match = re.search(r"token=([^&\s]+)", email.body)
        assert match is not None
        token = match.group(1)  # Extract captured token value

        # Step 4 — Call verification endpoint with extracted token
        verify_url = reverse("verify-email")
        verify_response = api_client.get(verify_url, {"token": token})

        assert verify_response.status_code == 200

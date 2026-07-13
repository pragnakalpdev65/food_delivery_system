import pytest
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.constants.cache_keys import CacheKey
from apps.core.constants.choices import UserType

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="emailuser",
        email="old@example.com",
        password="securepass123!",
        is_verified=True,
        user_type=UserType.CUSTOMER,
    )


@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.mark.django_db
class TestEmailChangeFlow:
    def test_full_email_change_via_query_token(self, auth_client, user, api_client):
        # Step 1: request change
        response = auth_client.post(
            reverse("email-change-request"),
            {
                "current_password": "securepass123!",
                "new_email": "new@example.com",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        old_token = signing.dumps({"user_id": str(user.id)}, salt="current-email")
        new_token = signing.dumps({"user_id": str(user.id)}, salt="new-email")

        # Step 2: confirm old email via GET ?token= (matches email link / frontend)
        old_resp = api_client.get(
            reverse("current-email-confirm"),
            {"token": old_token},
        )
        assert old_resp.status_code == status.HTTP_200_OK

        # Step 3: confirm new email via GET ?token=
        new_resp = api_client.get(
            reverse("confirm-email-change"),
            {"token": new_token},
        )
        assert new_resp.status_code == status.HTTP_200_OK
        assert "Email updated successfully" in new_resp.data["message"]

        user.refresh_from_db()
        assert user.email == "new@example.com"
        assert user.is_verified is False

    def test_new_email_confirm_requires_old_first(self, auth_client, user, api_client):
        auth_client.post(
            reverse("email-change-request"),
            {
                "current_password": "securepass123!",
                "new_email": "new2@example.com",
            },
            format="json",
        )
        new_token = signing.dumps({"user_id": str(user.id)}, salt="new-email")

        response = api_client.get(
            reverse("confirm-email-change"),
            {"token": new_token},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_legacy_old_token_body_still_works(self, auth_client, user, api_client):
        auth_client.post(
            reverse("email-change-request"),
            {
                "current_password": "securepass123!",
                "new_email": "legacy@example.com",
            },
            format="json",
        )
        old_token = signing.dumps({"user_id": str(user.id)}, salt="current-email")

        response = api_client.post(
            reverse("current-email-confirm"),
            {"old_token": old_token},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        mail_key = CacheKey.EMAIL_CHANGE % "old@example.com"
        assert cache.get(mail_key)["old_confirmed"] is True

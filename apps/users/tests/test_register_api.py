import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.users.api.v1.serializers.register import UserRegistrationSerializer

User = get_user_model()

@pytest.mark.django_db
class TestUserRegistrationAPI:

    def test_successful_user_registration(self, api_client):
        """Successful user registration with all valid fields."""

        url = reverse("register")
        payload = {
            "email": "createtest@example.com",
            "password":"TestuserPass123!",
            "username":"TestUser",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "9876543211",
            "user_type":"customer",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == payload["email"]

        user = User.objects.get(email=payload["email"])
        assert user.check_password(payload["password"]) is True
        assert user.phone_number == payload["phone_number"]
        assert user.is_active is True

    def test_email_uniqueness_validation(self, api_client):
        """Registration should fail if email already exists."""

        User.objects.create_user(
            email="duplicate@example.com",
            password="ExistingPass123!",
            username="DuplicateUser",
        )
        url = reverse("register")
        payload = {
            "email": "duplicate@example.com",
            "password": "AnotherPass123!",
            "username":"testuser",
            "first_name": "Test",
            "last_name": "User",
            "user_type":"customer",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data["errors"]
        
    def test_username_uniqueness_validation(self, api_client):
        """Registration should fail if email already exists."""

        User.objects.create_user(
            email="duplicate@example.com",
            password="ExistingPass123!",
            username="DuplicateUser",
        )
        url = reverse("register")
        payload = {
            "email": "test@example.com",
            "password": "AnotherPass123!",
            "username":"DuplicateUser",
            "first_name": "Test",
            "last_name": "User",
            "user_type":"customer",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response.data["errors"]

    def test_password_validation(self, api_client):
        """Registration fail if password does not match strength rules."""

        payload = {
            "email": "weakpass@example.com",
            "password": "123",
            "username":"DuplicateUser",
            "first_name": "Test",
            "last_name": "User",
            "user_type":"customer",
        }
        serializer = UserRegistrationSerializer(data=payload)
        assert serializer.is_valid() is False
        assert "password" in serializer.errors

    def test_optional_phone_number_handling(self, api_client):
        """User can register without phone number"""

        url = reverse("register")
        payload = {
            "email": "nophone@example.com",
            "password": "Nophonepass123!",
            "username":"DuplicateUser",
            "first_name": "Test",
            "last_name": "User",
            "user_type":"customer",
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email=payload["email"])
        assert user.phone_number in [None, ""]

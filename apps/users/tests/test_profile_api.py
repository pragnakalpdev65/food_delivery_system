import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.api.v1.serializers.profile import ChangePasswordSerializer
from apps.users.models.profile import CustomerProfile, DriverProfile, Address
from apps.core.constants.messages import AuthMessages

# Get active User model (supports custom user model)
User = get_user_model()

@pytest.fixture
def user():
    user = User.objects.create_user(
        email="test@example.com",
        password="securepass123!",
        username="TestUser",
        is_verified=True,
        user_type="customer",
    )
    return user

@pytest.fixture
def driver_user():
    user = User.objects.create_user(
        username="driver@example.com",
        email="driver@example.com",
        password="securepass123!",
        is_verified=True,
        user_type="driver",
    )
    return user

@pytest.fixture
def authenticated_client(api_client, user):
    """Client authenticated with user token."""
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client

@pytest.fixture
def driver_authenticated_client(api_client, driver_user):
    """Client authenticated with driver token."""
    refresh = RefreshToken.for_user(driver_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client

@pytest.mark.django_db
class TestChangePasswordAPI:
    """
    Test Suite: Change Password API
    Purpose:
    Validate password change functionality including:
    - Successful password update
    - Incorrect current password handling
    - Preventing same password reuse
    - Password validation enforcement
    - Token invalidation after password change
    """

    def test_change_password_success(self, api_client, user):
        """Should successfully change password when valid credentials provided."""
        url = reverse("change-password")
        refresh = RefreshToken.for_user(user)  # Generate JWT token for authentication
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {
            "current_password": "securepass123!",
            "new_password": "NewStrongPass@123!",
            "confirm_password": "NewStrongPass@123!",
        }
        response = api_client.post(url, payload, format="json")
        assert "Password changed successfully.Please login again." in response.data
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()  # Reload user from DB and verify password actually changed
        assert user.check_password("NewStrongPass@123!")

    def test_wrong_current_password(self, api_client, user):
        """Should return error if current password is incorrect."""
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {
            "current_password": "wrongpassword",
            "new_password": "securepass123!",
            "confirm_password": "securepass123!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False
        assert "Current password is incorrect." in serializer.errors["non_field_errors"][0]

    def test_password_cannot_same(self, api_client, user):
        """Should reject request if new password equals current password."""
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {
            "current_password": "securepass123!",
            "new_password": "securepass123!",
            "confirm_password": "securepass123!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False
        assert (
            "New password must be different from current password."
            in serializer.errors["non_field_errors"][0]
        )

    def test_confirm_password_same_as_new_password(self, api_client, user):
        """Should fail validation if confirm_password does not match new_password."""
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {
            "current_password": "securepass123!",
            "new_password": "securepass1234!",
            "confirm_password": "secure123!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False
        assert (
            "New password and Current password does not match."
            in serializer.errors["non_field_errors"][0]
        )

    def test_new_password_validations(self, api_client, user):
        """Should fail if new password does not meet validation rules."""
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {
            "current_password": "securepass123!",
            "new_password": "sec4!",
            "confirm_password": "securepass1234!",
        }
        serializer = ChangePasswordSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False
        assert "new_password" in serializer.errors

    def test_tokens_blacklisted_after_password_change(self, api_client, user):
        """
        Should:
        - Successfully change password
        - Invalidate all existing tokens
        - Blacklist refresh tokens
        """
        url = reverse("change-password")
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        payload = {
            "current_password": "securepass123!",
            "new_password": "NewStrongPass@123!",
            "confirm_password": "NewStrongPass@123!",
        }
        response = api_client.post(url, payload, format="json")
        user.refresh_from_db()  # Ensure password updated in database
        assert user.check_password("NewStrongPass@123!")
        assert response.status_code == status.HTTP_200_OK
        outstanding = OutstandingToken.objects.filter(user=user)
        blacklisted = BlacklistedToken.objects.filter(token__user=user)
        assert outstanding.count() == blacklisted.count()
        assert "Password changed successfully.Please login again." in response.data

@pytest.mark.django_db
class TestCustomerProfileAPI:
    """
    Test Suite: Customer Profile API
    Purpose:
    Validate customer profile retrieval and update functionality.
    """
    def test_get_customer_profile_success(self, authenticated_client, user):
        """Should retrieve customer profile when authenticated."""
        # Create customer profile
        profile = CustomerProfile.objects.get(user=user)          
        url = reverse("customer-profile")
        response = authenticated_client.get(url)
        assert response.data["id"] == str(profile.id)
        assert response.data["user"] == user.id

    def test_get_customer_profile_not_found(self, driver_authenticated_client):
        """Should return 404 when customer profile doesn't exist."""
        url = reverse("customer-profile")
        response = driver_authenticated_client.get(url)
        assert "Customer profile not found" in response.data["detail"]

    def test_get_customer_profile_without_authentication(self, api_client):
        """Should return 401 when not authenticated."""
        url = reverse("customer-profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_customer_profile_success(self, authenticated_client, user):
        """Should update customer profile with valid data."""
        profile = CustomerProfile.objects.get(user=user)
        url = reverse("customer-profile")
        payload = {
            "default_address": None,
        }
        response = authenticated_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()

@pytest.mark.django_db
class TestDriverProfileAPI:
    """
    Test Suite: Driver Profile API
    Purpose:
    Validate driver profile retrieval and update functionality.
    """
    def test_get_driver_profile_success(self, driver_authenticated_client, driver_user):
        """Should retrieve driver profile when authenticated."""
        profile = DriverProfile.objects.create(
            user=driver_user,
            vehicle_type="car",
            vehicle_number="ABC123",
            license_number="DL123456"
        )
        url = reverse("driver-profile")
        response = driver_authenticated_client.get(url)
        assert response.data["id"] == str(profile.id)

    def test_get_driver_profile_not_found(self, driver_authenticated_client):
        """Should return 404 when driver profile doesn't exist."""
        url = reverse("driver-profile")
        response = driver_authenticated_client.get(url)
        assert "Driver profile not found" in response.data["detail"]

    def test_update_driver_profile_success(self, driver_authenticated_client, driver_user):
        """Should update driver profile with valid data."""
        profile = DriverProfile.objects.create(
            user=driver_user,
            vehicle_type="car",
            vehicle_number="ABC123",
            license_number="DL123456"
        )
        url = reverse("driver-profile")
        payload = {
            "vehicle_number": "XYZ789",
            "vehicle_type": "bike"
        }
        response = driver_authenticated_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        profile.refresh_from_db()
        assert profile.vehicle_number == "XYZ789"
        assert profile.vehicle_type == "bike"

    def test_update_driver_profile_not_found(self, driver_authenticated_client):
        """Should return 404 when updating non-existent driver profile."""
        url = reverse("driver-profile")
        payload = {
            "vehicle_number": "XYZ789",
        }
        response = driver_authenticated_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestAddressAPI:
    """
    Test Suite: Address API
    Purpose:
    Validate address listing and creation functionality.
    """
    def test_get_addresses_success(self, authenticated_client, user):
        """Should list all addresses for authenticated user."""
        profile = CustomerProfile.objects.get(user=user)
        Address.objects.create(
            customer=profile,
            address="123 Main St",
            label="Home",
            pin_code="12345"
        )
        Address.objects.create(
            customer=profile,
            address="456 Work Ave",
            label="Work",
            pin_code="67890"
        ) 
        url = reverse("address-list-create")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_create_address_success(self, authenticated_client, user):
        """Should create new address for authenticated user."""
        profile = CustomerProfile.objects.get(user=user)
        url = reverse("address-list-create")
        payload = {
            "address": "789 New St",
            "label": "Home",
            "pin_code": "99999"
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.data["address"] == "789 New St"
        assert Address.objects.filter(customer=profile).count() == 1

    def test_create_address_missing_required_fields(self, authenticated_client, user):
        """Should fail when required fields are missing."""
        profile = CustomerProfile.objects.get(user=user) 
        url = reverse("address-list-create")
        payload = {
            "label": "Home"
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_address_without_authentication(self, api_client):
        """Should return 401 when not authenticated."""
        url = reverse("address-list-create")
        payload = {
            "address": "789 New St",
            "label": "Home",
            "pin_code": "99999"
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestAddressDetailAPI:
    """
    Test Suite: Address Detail API
    Purpose:
    Validate address retrieval, update, and deletion functionality.
    """
    
    @pytest.fixture
    def customer_profile(self, user):
        """Create customer profile with address."""
        return CustomerProfile.objects.get(user=user)

    @pytest.fixture
    def address(self, customer_profile):
        """Create an address."""
        return Address.objects.create(
            customer=customer_profile,
            address="123 Main St",
            label="Home",
            pin_code="12345"
        )

    def test_get_address_success(self, authenticated_client, address):
        """Should retrieve address detail when authenticated."""
        url = reverse("address-detail", kwargs={"pk": address.id})
        response = authenticated_client.get(url)
        assert response.data["id"] == str(address.id)
        assert response.data["address"] == "123 Main St"

    def test_get_address_not_found(self, authenticated_client):
        """Should return 404 when address doesn't exist."""
        url = reverse("address-detail", kwargs={"pk": "7e45306a-763b-4a78-aefa-1ba672cef648"})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_address_of_different_user(self, authenticated_client, user):
        """Should not get address of another user."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="pass123!",
            user_type="customer"
        )
        other_profile = CustomerProfile.objects.get(user=other_user)
        other_address = Address.objects.create(
            customer=other_profile,
            address="999 Other St",
            label="Other",
            pin_code="55555"
        )
        url = reverse("address-detail", kwargs={"pk": other_address.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_address_success(self, authenticated_client, address):
        """Should update address with valid data."""
        url = reverse("address-detail", kwargs={"pk": address.id})
        payload = {
            "address": "999 Updated St",
            "label": "Work"
        }
        response = authenticated_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        address.refresh_from_db()
        assert address.address == "999 Updated St"
        assert address.label == "Work"

    def test_update_address_not_found(self, authenticated_client):
        """Should return 404 when updating non-existent address."""
        url = reverse("address-detail", kwargs={"pk": "7e45306a-763b-4a78-aefa-1ba672cef648"})
        payload = {
            "address": "999 Updated St"
        }
        response = authenticated_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_partial_update_address(self, authenticated_client, address):
        """Should allow partial update of address."""
        url = reverse("address-detail", kwargs={"pk": address.id})
        payload = {
            "label": "Office"
        }
        response = authenticated_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        address.refresh_from_db()
        assert address.label == "Office"
        assert address.address == "123 Main St"  # Should remain unchanged

    def test_delete_address_success(self, authenticated_client, address):
        """Should delete address successfully."""
        address_id = address.id
        url = reverse("address-detail", kwargs={"pk": address_id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Address.objects.filter(id=address_id).exists()

    def test_delete_address_not_found(self, authenticated_client):
        """Should return 404 when deleting non-existent address."""
        url = reverse("address-detail", kwargs={"pk": "7e45306a-763b-4a78-aefa-1ba672cef648"})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_address_of_different_user(self, authenticated_client, user):
        """Should not delete address of another user."""
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="pass123!",
            user_type="customer"
        )
        other_profile = CustomerProfile.objects.get(user=other_user)
        other_address = Address.objects.create(
            customer=other_profile,
            address="999 Other St",
            label="Other",
            pin_code="55555"
        )
        url = reverse("address-detail", kwargs={"pk": other_address.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Address.objects.filter(id=other_address.id).exists()

@pytest.mark.django_db
class TestUpdateEmailAPI:
    """
    Test Suite: Update Email API
    Purpose:
    Validate email change request initiation.
    """

    def test_update_email_request_success(self, authenticated_client, user):
        """Should initiate email change request when valid credentials provided."""
        url = reverse("email-change-request")
        payload = {
            "current_password": "securepass123!",
            "new_email": "newemail@example.com"
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.data["message"] == "Verification emails sent to current and new address"

    def test_update_email_with_wrong_password(self, authenticated_client, user):
        """Should fail with incorrect current password."""
        from apps.users.api.v1.serializers.profile import UpdateEmailSerializer
        payload = {
            "current_password": "wrongpassword",
            "new_email": "newemail@example.com"
        }
        serializer = UpdateEmailSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False

    def test_update_email_with_existing_email(self, authenticated_client, user):
        """Should fail when new email is already registered."""
        from apps.users.api.v1.serializers.profile import UpdateEmailSerializer
        User.objects.create_user(
            username="existing@example.com",
            email="existing@example.com",
            password="pass123!",
            user_type="customer"
        )
        payload = {
            "current_password": "securepass123!",
            "new_email": "existing@example.com"
        }
        serializer = UpdateEmailSerializer(data=payload, context={"user": user})
        assert serializer.is_valid() is False
        assert "An account with this email already exists." in str(serializer.errors["new_email"][0])

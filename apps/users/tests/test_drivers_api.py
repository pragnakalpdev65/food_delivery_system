import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.constants.choices import UserType

User = get_user_model()


@pytest.fixture
def restaurant_owner(db):
    return User.objects.create_user(
        username="owner@example.com",
        email="owner@example.com",
        password="securepass123!",
        is_verified=True,
        user_type=UserType.RESTAURANT_OWNER,
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="customer@example.com",
        email="customer@example.com",
        password="securepass123!",
        is_verified=True,
        user_type=UserType.CUSTOMER,
    )


@pytest.fixture
def delivery_driver_user(db):
    return User.objects.create_user(
        username="driver_user",
        email="driver_user@example.com",
        password="securepass123!",
        is_verified=True,
        user_type=UserType.DELIVERY_DRIVER,
    )


def _configure_driver_profile(user, **fields):
    """Update auto-created DriverProfile from the user post_save signal."""
    profile = user.driver_profile
    for attr, value in fields.items():
        setattr(profile, attr, value)
    profile.save()
    return profile


@pytest.fixture
def available_driver(db):
    user = User.objects.create_user(
        username="available_driver",
        email="available_driver@example.com",
        password="securepass123!",
        is_verified=True,
        user_type=UserType.DELIVERY_DRIVER,
        phone_number="1111111111",
    )
    _configure_driver_profile(
        user,
        vehicle_type="bike",
        vehicle_number="BIKE1",
        license_number="LIC1",
        is_available=True,
        total_deliveries=12,
        average_rating="4.50",
    )
    return user


@pytest.fixture
def unavailable_driver(db):
    user = User.objects.create_user(
        username="busy_driver",
        email="busy_driver@example.com",
        password="securepass123!",
        is_verified=True,
        user_type=UserType.DELIVERY_DRIVER,
        phone_number="2222222222",
    )
    _configure_driver_profile(
        user,
        vehicle_type="car",
        vehicle_number="CAR1",
        license_number="LIC2",
        is_available=False,
    )
    return user


@pytest.fixture
def inactive_driver(db):
    user = User.objects.create_user(
        username="inactive_driver",
        email="inactive_driver@example.com",
        password="securepass123!",
        is_verified=True,
        is_active=False,
        user_type=UserType.DELIVERY_DRIVER,
        phone_number="3333333333",
    )
    _configure_driver_profile(
        user,
        vehicle_type="scooter",
        vehicle_number="SCOOT1",
        license_number="LIC3",
        is_available=True,
    )
    return user


@pytest.fixture
def owner_client(api_client, restaurant_owner):
    refresh = RefreshToken.for_user(restaurant_owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def customer_client(api_client, customer):
    refresh = RefreshToken.for_user(customer)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def driver_client(api_client, delivery_driver_user):
    refresh = RefreshToken.for_user(delivery_driver_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.mark.django_db
class TestDriverListAPI:
    def test_owner_can_list_drivers(
        self, owner_client, available_driver, unavailable_driver
    ):
        url = reverse("driver-list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

        driver_ids = {item["driver_id"] for item in response.data["results"]}
        assert str(available_driver.id) in driver_ids
        assert str(unavailable_driver.id) in driver_ids

    def test_list_response_fields(self, owner_client, available_driver):
        url = reverse("driver-list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        item = response.data["results"][0]
        expected_fields = {
            "driver_id",
            "username",
            "email",
            "phone_number",
            "vehicle_type",
            "vehicle_number",
            "is_available",
            "total_deliveries",
            "average_rating",
        }
        assert expected_fields.issubset(item.keys())
        assert item["driver_id"] == str(available_driver.id)
        assert item["username"] == "available_driver"
        assert item["email"] == "available_driver@example.com"
        assert item["phone_number"] == "1111111111"
        assert item["vehicle_type"] == "bike"
        assert item["vehicle_number"] == "BIKE1"
        assert item["is_available"] is True
        assert item["total_deliveries"] == 12
        assert item["average_rating"] == "4.50"

    def test_filter_by_is_available_true(
        self, owner_client, available_driver, unavailable_driver
    ):
        url = reverse("driver-list")
        response = owner_client.get(url, {"is_available": True})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["driver_id"] == str(available_driver.id)
        assert response.data["results"][0]["is_available"] is True

    def test_filter_by_is_available_false(
        self, owner_client, available_driver, unavailable_driver
    ):
        url = reverse("driver-list")
        response = owner_client.get(url, {"is_available": False})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["driver_id"] == str(unavailable_driver.id)
        assert response.data["results"][0]["is_available"] is False

    def test_excludes_inactive_drivers(
        self, owner_client, available_driver, inactive_driver
    ):
        url = reverse("driver-list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        driver_ids = {item["driver_id"] for item in response.data["results"]}
        assert str(available_driver.id) in driver_ids
        assert str(inactive_driver.id) not in driver_ids

    def test_excludes_non_driver_users(self, owner_client, available_driver, customer):
        url = reverse("driver-list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        driver_ids = {item["driver_id"] for item in response.data["results"]}
        assert str(customer.id) not in driver_ids
        assert len(response.data["results"]) == 1

    def test_empty_list_when_no_drivers(self, owner_client):
        url = reverse("driver-list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []
        assert response.data["count"] == 0

    def test_available_drivers_sorted_first(
        self, owner_client, available_driver, unavailable_driver
    ):
        url = reverse("driver-list")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["is_available"] is True
        assert response.data["results"][0]["driver_id"] == str(available_driver.id)

    def test_customer_cannot_list_drivers(self, customer_client, available_driver):
        url = reverse("driver-list")
        response = customer_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_driver_cannot_list_drivers(self, driver_client, available_driver):
        url = reverse("driver-list")
        response = driver_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_list_drivers(self, api_client, available_driver):
        url = reverse("driver-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

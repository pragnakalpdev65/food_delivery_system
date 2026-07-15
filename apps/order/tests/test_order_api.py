import uuid

import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from apps.users.models import CustomUser
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem
from apps.order.models.order import Order
from apps.core.constants.choices import OrderStatus
from apps.core.constants.choices import UserType


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def customer(db):
    uid = uuid.uuid4().hex[:8]
    return CustomUser.objects.create_user(
        username=f"customer_{uid}",
        email=f"customer_{uid}@example.com",
        password="pass123",
        user_type=UserType.CUSTOMER
    )

@pytest.fixture
def owner(db):
    uid = uuid.uuid4().hex[:8]
    return CustomUser.objects.create_user(
        username=f"owner_{uid}",
        email=f"owner_{uid}@example.com",
        password="pass123",
        user_type=UserType.RESTAURANT_OWNER,
        is_verified=True,
    )

@pytest.fixture
def driver(db):
    uid = uuid.uuid4().hex[:8]
    return CustomUser.objects.create_user(
        username=f"driver_{uid}",
        email=f"driver_{uid}@example.com",
        password="pass123",
        user_type=UserType.DELIVERY_DRIVER
    )

@pytest.fixture
def restaurant(db, owner):
    return Restaurant.objects.create(
        owner=owner,
        name="Test Restaurant",
        delivery_fee=50,
        opening_time = "10:00:00",
        closing_time = "17:00:00"
    )


@pytest.fixture
def menu_item(db, restaurant):
    return MenuItem.objects.create(
        restaurant=restaurant,
        name="Burger",
        price=100
    )


@pytest.fixture
def order(db, customer, restaurant):
    return Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        delivery_address="Test Address",
        status=OrderStatus.PENDING
    )


@pytest.mark.django_db
class TestOrderAPI:
    def test_orders_list_is_paginated(self, customer, order, client):
        client.force_authenticate(user=customer)

        url = reverse("orders-list")
        response = client.get(url)

        assert response.status_code == 200
        assert "results" in response.data
        assert "count" in response.data
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_valid_status_transition(self, owner, order, client):
        client.force_authenticate(user=owner)

        url = reverse('orders-update-status', args=[order.id])

        response = client.post(url, {"status": OrderStatus.CONFIRMED}, format='json')
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CONFIRMED


    def test_invalid_status_transition(self, owner, order, client):
        client.force_authenticate(user=owner)

        url = reverse('orders-update-status', args=[order.id])

        response = client.post(url, {"status": "DELIVERED"}, format='json')
        assert response.data["code"] == "invalid_transition"

    def test_owner_can_assign_driver(self, owner, driver, order, client):
        order.status = OrderStatus.READY
        order.save()

        client.force_authenticate(user=owner)

        url = reverse('orders-assign-driver', args=[order.id])
        
        response = client.post(url, {"driver_id": driver.id}, format='json')
        assert response.status_code == 200
        order.refresh_from_db()

        assert order.driver == driver
        assert order.status == OrderStatus.PICKED_UP

    def test_cannot_assign_driver_twice(self, owner, driver, order, client):
        order.status = OrderStatus.READY
        order.driver = driver
        order.save()

        client.force_authenticate(user=owner)

        url = reverse('orders-assign-driver', args=[order.id])
        response = client.post(url, {"driver_id": driver.id}, format='json')

        assert response.data["code"] == "already_assigned"


    def test_missing_status_field(self, owner, order, client):
        client.force_authenticate(user=owner)

        url = reverse('orders-update-status', args=[order.id])
        response = client.post(url, {}, format='json')

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# is_available lifecycle tests
# ---------------------------------------------------------------------------

@pytest.fixture
def driver_with_profile(db):
    """Driver user whose DriverProfile is auto-created by the post_save signal."""
    uid = uuid.uuid4().hex[:8]
    user = CustomUser.objects.create_user(
        username=f"driver_{uid}",
        email=f"driver_{uid}@example.com",
        password="pass123",
        user_type=UserType.DELIVERY_DRIVER,
    )
    # Signal creates DriverProfile automatically — no manual create needed.
    return user


@pytest.mark.django_db
class TestDriverAvailabilityLifecycle:
    """
    Tests the full is_available lifecycle:
      True (default) → False (on assign) → True (on DELIVERED)
    """

    def test_driver_is_available_by_default(self, driver_with_profile):
        """DriverProfile starts with is_available=True."""
        assert driver_with_profile.driver_profile.is_available is True

    def test_assign_driver_sets_unavailable(self, owner, driver_with_profile, order, client):
        """After assign_driver, driver's is_available must become False."""
        order.status = OrderStatus.READY
        order.save()

        client.force_authenticate(user=owner)
        url = reverse("orders-assign-driver", args=[order.id])
        response = client.post(url, {"driver_id": driver_with_profile.id}, format="json")

        assert response.status_code == 200
        driver_with_profile.driver_profile.refresh_from_db()
        assert driver_with_profile.driver_profile.is_available is False

    def test_cannot_assign_unavailable_driver(self, owner, driver_with_profile, restaurant, customer, client):
        """A driver with is_available=False must be rejected with 400."""
        driver_with_profile.driver_profile.update_availability(False)

        # Create a fresh READY order
        order = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_address="Some Street",
            status=OrderStatus.READY,
        )

        client.force_authenticate(user=owner)
        url = reverse("orders-assign-driver", args=[order.id])
        response = client.post(url, {"driver_id": driver_with_profile.id}, format="json")

        assert response.status_code == 400
        assert response.data["code"] == "driver_unavailable"

    def test_delivered_resets_driver_to_available(self, owner, driver_with_profile, order, client):
        """When order status reaches DELIVERED, driver's is_available resets to True."""
        # Assign the driver (sets is_available=False)
        order.status = OrderStatus.READY
        order.save()

        client.force_authenticate(user=owner)
        assign_url = reverse("orders-assign-driver", args=[order.id])
        client.post(assign_url, {"driver_id": driver_with_profile.id}, format="json")

        driver_with_profile.driver_profile.refresh_from_db()
        assert driver_with_profile.driver_profile.is_available is False  # sanity check

        # Now move to DELIVERED
        order.refresh_from_db()
        status_url = reverse("orders-update-status", args=[order.id])
        response = client.post(status_url, {"status": OrderStatus.DELIVERED}, format="json")

        assert response.status_code == 200
        driver_with_profile.driver_profile.refresh_from_db()
        assert driver_with_profile.driver_profile.is_available is True

    def test_assign_driver_with_nonexistent_driver_id(self, owner, order, client):
        """Passing a random UUID that doesn't exist must return 404."""
        order.status = OrderStatus.READY
        order.save()

        client.force_authenticate(user=owner)
        url = reverse("orders-assign-driver", args=[order.id])
        response = client.post(url, {"driver_id": uuid.uuid4()}, format="json")

        assert response.status_code == 404
        assert response.data["code"] == "driver_profile_not_found"
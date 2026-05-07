import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from apps.users.models import CustomUser
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem
from apps.order.models.order import Order
from apps.core.constants.status import OrderStatus
from apps.core.constants.user_types import UserType


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def customer(db):
    return CustomUser.objects.create_user(
        username="customer",
        email="customer@example.com",  
        password="pass123",
        user_type=UserType.CUSTOMER
    )

@pytest.fixture
def owner(db):
    return CustomUser.objects.create_user(
        username="owner",
        email="owner@example.com",     
        password="pass123",
        user_type=UserType.RESTAURANT_OWNER
    )

@pytest.fixture
def driver(db):
    return CustomUser.objects.create_user(
        username="driver",
        email="driver@example.com",    
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


    def test_customer_can_cancel_pending_order(self, customer, order, client):
        client.force_authenticate(user=customer)

        url = reverse('orders-cancel', args=[order.id])

        response = client.post(url)
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED


    def test_cannot_cancel_after_preparing(self, customer, order, client):
        order.status = OrderStatus.PREPARING
        order.save()

        client.force_authenticate(user=customer)

        url = reverse('orders-cancel', args=[order.id])
        response = client.post(url)

        assert response.data["code"] == "can_not_be_cancelled"

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
        
    def test_driver_cannot_cancel_order(self, driver, order, client):
        client.force_authenticate(user=driver)

        url = reverse('orders-cancel', args=[order.id])
        response = client.post(url)

        assert response.status_code == 403


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
        
        
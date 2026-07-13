import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.constants.choices import OrderStatus, UserType
from apps.order.models.order import Order, OrderItem
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        username="dash_owner",
        email="dash_owner@example.com",
        password="pass123!",
        user_type=UserType.RESTAURANT_OWNER,
        is_verified=True,
    )


@pytest.fixture
def customer(db):
    return User.objects.create_user(
        username="dash_customer",
        email="dash_customer@example.com",
        password="pass123!",
        user_type=UserType.CUSTOMER,
        is_verified=True,
    )


@pytest.fixture
def restaurant(db, owner):
    return Restaurant.objects.create(
        owner=owner,
        name="Dashboard Restaurant",
        email="dash-restaurant@example.com",
        address="Surat",
        opening_time="10:00:00",
        closing_time="22:00:00",
        average_rating="4.25",
    )


@pytest.fixture
def menu_item(db, restaurant):
    return MenuItem.objects.create(
        restaurant=restaurant,
        name="Pizza",
        price="200.00",
        category="main_course",
        preparation_time=20,
    )


@pytest.fixture
def owner_client(api_client, owner):
    refresh = RefreshToken.for_user(owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def customer_client(api_client, customer):
    refresh = RefreshToken.for_user(customer)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.mark.django_db
class TestRestaurantDashboardAPI:
    def test_dashboard_metrics(
        self, owner_client, restaurant, menu_item, customer
    ):
        Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_address="Addr",
            status=OrderStatus.PREPARING,
            total_amount="100.00",
        )
        delivered = Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_address="Addr",
            status=OrderStatus.DELIVERED,
            total_amount="250.00",
            actual_delivery_time=timezone.now(),
        )
        OrderItem.objects.create(
            order=delivered,
            menu_item=menu_item,
            quantity=2,
            price="125.00",
        )

        url = reverse(
            "restaurant-dashboard",
            kwargs={"restaurant_id": restaurant.id},
        )
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["active_orders"] == 1
        assert response.data["daily_revenue"] == "250.00"
        assert response.data["new_customers"] == 1
        assert response.data["total_menu_items"] == 1
        assert response.data["net_revenue"] == "250.00"
        assert response.data["total_orders"] == 2
        assert response.data["average_order_value"] == "250.00"
        assert response.data["average_rating"] == "4.25"
        assert "revenue_trends" in response.data["analytics"]
        assert "sales_by_category" in response.data["analytics"]
        assert "popular_times" in response.data["analytics"]
        assert response.data["analytics"]["sales_by_category"][0]["category"] == (
            "main_course"
        )

    def test_dashboard_forbidden_for_customer(
        self, customer_client, restaurant
    ):
        url = reverse(
            "restaurant-dashboard",
            kwargs={"restaurant_id": restaurant.id},
        )
        response = customer_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_dashboard_not_found_for_other_owner(self, api_client, restaurant):
        other = User.objects.create_user(
            username="other_owner",
            email="other_owner@example.com",
            password="pass123!",
            user_type=UserType.RESTAURANT_OWNER,
        )
        refresh = RefreshToken.for_user(other)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        url = reverse(
            "restaurant-dashboard",
            kwargs={"restaurant_id": restaurant.id},
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.constants.choices import UserType, OrderStatus
from apps.order.models.order import Order
from apps.restaurant.models.restaurant import Restaurant
from apps.users.models.profile import RestaurantOwnerProfile

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
def owner_client(api_client, restaurant_owner):
    refresh = RefreshToken.for_user(restaurant_owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def customer_client(api_client, customer):
    refresh = RefreshToken.for_user(customer)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.mark.django_db
class TestRestaurantOwnerProfileAPI:
    def test_profile_created_on_owner_registration(self, restaurant_owner):
        assert RestaurantOwnerProfile.objects.filter(user=restaurant_owner).exists()

    def test_get_owner_profile_success(self, owner_client, restaurant_owner):
        url = reverse("restaurant-owner-profile")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "business_name" in response.data
        assert "total_restaurants" in response.data
        assert "total_orders" in response.data
        assert "total_revenue" in response.data
        assert "average_rating" in response.data

    def test_get_owner_profile_without_existing_row(self, owner_client, restaurant_owner):
        # Simulate legacy owners who registered before auto-create existed.
        RestaurantOwnerProfile.objects.filter(user=restaurant_owner).delete()

        url = reverse("restaurant-owner-profile")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert RestaurantOwnerProfile.objects.filter(user=restaurant_owner).exists()

    def test_get_owner_profile_with_stats(
        self, owner_client, restaurant_owner, customer
    ):
        restaurant = Restaurant.objects.create(
            owner=restaurant_owner,
            name="Stats Restaurant",
            email="stats-restaurant@example.com",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00",
            average_rating="4.50",
        )
        Order.objects.create(
            customer=customer,
            restaurant=restaurant,
            delivery_address="Test Address",
            status=OrderStatus.DELIVERED,
            total_amount="250.00",
        )

        url = reverse("restaurant-owner-profile")
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_restaurants"] == 1
        assert response.data["total_orders"] == 1
        assert response.data["total_revenue"] == "250.00"
        assert response.data["average_rating"] == "4.50"

    def test_update_owner_profile(self, owner_client):
        url = reverse("restaurant-owner-profile")
        response = owner_client.put(
            url,
            {
                "business_name": "Food Corp",
                "contact_number": "9876543210",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["business_name"] == "Food Corp"
        assert response.data["contact_number"] == "9876543210"

    def test_post_owner_profile_update(self, owner_client):
        url = reverse("restaurant-owner-profile")
        response = owner_client.post(
            url,
            {
                "business_name": "Post Corp",
                "contact_number": "9123456780",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["business_name"] == "Post Corp"
        assert response.data["contact_number"] == "9123456780"

    def test_customer_cannot_get_owner_profile(self, customer_client):
        url = reverse("restaurant-owner-profile")
        response = customer_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.order.models.order import Order, Review
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem

User = get_user_model()


@pytest.mark.django_db
class TestReviewAPI:

    def setup_method(self):
        self.customer = User.objects.create_user(
            email="customer@test.com",
            password="Testpass123!",
            username="customer",
            user_type="customer"
        )

        self.other_user = User.objects.create_user(
            email="other@test.com",
            password="Testpass123!",
            username="other",
            user_type="customer"
        )

        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="Testpass123!",
            username="owner",
            user_type="restaurant_owner"
        )

        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Test Restaurant",
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        self.menu_item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="300.00",
            category="main_course",
            preparation_time="00:20:00"
        )

        self.order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            delivery_address="Test Address",
            status="delivered"
        )

        self.url = reverse("Review")

    def test_create_review_success(self, api_client):
        api_client.force_authenticate(user=self.customer)

        payload = {
            "order": str(self.order.id),
            "restaurant": str(self.restaurant.id),
            "menu_item": str(self.menu_item.id),
            "rating": 5,
            "comment": "Great food!"
        }

        response = api_client.post(self.url, payload)
        assert Review.objects.count() == 1

    def test_cannot_review_other_user_order(self, api_client):
        api_client.force_authenticate(user=self.other_user)

        payload = {
            "order": str(self.order.id),
            "restaurant": str(self.restaurant.id),
            "menu_item": str(self.menu_item.id),
            "rating": 4,
            "comment": "Nice"
        }

        response = api_client.post(self.url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "own order" in str(response.data)

    def test_cannot_review_non_delivered_order(self, api_client):
        api_client.force_authenticate(user=self.customer)

        self.order.status = "pending"
        self.order.save()

        payload = {
            "order": str(self.order.id),
            "restaurant": str(self.restaurant.id),
            "menu_item": str(self.menu_item.id),
            "rating": 3,
            "comment": "Okay"
        }

        response = api_client.post(self.url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "delivered" in str(response.data)

    def test_invalid_rating(self, api_client):
        api_client.force_authenticate(user=self.customer)
        
        payload = {
            "order": str(self.order.id),
            "restaurant": str(self.restaurant.id),
            "menu_item": str(self.menu_item.id),
            "rating": 6, 
            "comment": "Bad"
        }

        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_user(self, api_client):
        payload = {
            "order": str(self.order.id),
            "restaurant": str(self.restaurant.id),
            "menu_item": str(self.menu_item.id),
            "rating": 5,
            "comment": "Nice"
        }

        response = api_client.post(self.url, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
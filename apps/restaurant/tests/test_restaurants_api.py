import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.restaurant.models.restaurant import Restaurant

User = get_user_model()


@pytest.mark.django_db
class TestRestaurantAPI:

    def setup_method(self):
        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="Ownerpass123!",
            username="owner",
            user_type="Restaurant Owner"
        )

        self.customer = User.objects.create_user(
            email="customer@test.com",
            password="Customerpass123!",
            username="customer",
            user_type="Customer"
        )

    def test_create_restaurant_by_owner(self, api_client):
        api_client.force_authenticate(user=self.owner)

        url = reverse("restaurants-list")
        payload = {
            "name": "Test Restaurant",
            "cuisine_type": "indian",
            "address": "Surat",
            "opening_time": "10:00:00",
            "closing_time": "22:00:00",
            "delivery_fee": "30.00",
            "minimum_order": "100.00"
        }

        response = api_client.post(url, payload,format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Restaurant.objects.count() == 1

    def test_customer_cannot_create_restaurant(self, api_client):
        api_client.force_authenticate(user=self.customer)

        url = reverse("restaurants-list")
        payload = {
            "name": "Invalid Restaurant",
            "cuisine_type": "indian",
            "address": "Surat",
            "opening_time": "10:00:00",
            "closing_time": "22:00:00",
            "delivery_fee": "30.00",
            "minimum_order": "100.00"
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_restaurants(self, api_client):
        Restaurant.objects.create(
            owner=self.owner,
            name="Test Restaurant",
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        url = reverse("restaurants-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 1

    def test_search_restaurant(self, api_client):
        Restaurant.objects.create(
            owner=self.owner,
            name="Spicy Hub",
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        url = reverse("restaurants-list") + "?search=Spicy"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 1

    def test_filter_restaurant_by_cuisine(self, api_client):
        Restaurant.objects.create(
            owner=self.owner,
            name="Italian Hub",
            cuisine_type="italian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        url = reverse("restaurants-list") + "?cuisine_type=italian"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 1
import pytest
from django.urls import reverse
from rest_framework import status
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestMenuItemAPI:

    def setup_method(self):
        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="Ownerpass123!",
            username="owner",
            user_type="restaurant_owner"
        )

        self.customer = User.objects.create_user(
            email="customer@test.com",
            password="Customerpass123!",
            username="customer",
            user_type="customer"
        )

        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Test Restaurant",
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

    def test_owner_can_create_menu_item(self, api_client):
        api_client.force_authenticate(user=self.owner)

        url = reverse("menuitem-list")
        payload = {
            "name": "Pizza",
            "price": "200.00",
            "category": "main_course",
            "restaurant": str(self.restaurant.id),
            "preparation_time": 20
        }

        response = api_client.post(url, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert MenuItem.objects.count() == 1

    def test_customer_cannot_create_menu_item(self, api_client):
        api_client.force_authenticate(user=self.customer)

        url = reverse("menuitem-list")
        payload = {
            "name": "Burger",
            "price": "100.00",
            "category": "main_course",
            "restaurant": str(self.restaurant.id),
            "preparation_time": 15
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_cannot_add_item_to_other_restaurant(self, api_client):
        other_owner = User.objects.create_user(
            email="other1@test.com",
            password="Testpass123!",
            username="other",
            user_type="restaurant_owner"
        )

        other_restaurant = Restaurant.objects.create(
            owner=other_owner,
            name="Other Restaurant",
            email="other_restaurant@test.com",    
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        api_client.force_authenticate(user=self.owner)

        url = reverse("menuitem-list")
        payload = {
            "name": "Dish",
            "price": "150.00",
            "category": "main_course",
            "restaurant": str(other_restaurant.id),
            "preparation_time": 10
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_menu_items(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time="00:20:00"
        )

        url = reverse("menuitem-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filter_menu_items(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time="00:20:00"
        )

        url = reverse("menuitem-list") + "?category=main_course"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
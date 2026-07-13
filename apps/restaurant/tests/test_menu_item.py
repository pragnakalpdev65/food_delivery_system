import uuid

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant

User = get_user_model()


@pytest.mark.django_db
class TestMenuItemAPI:

    def setup_method(self):
        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="Ownerpass123!",
            username="owner",
            user_type="restaurant_owner",
        )

        self.customer = User.objects.create_user(
            email="customer@test.com",
            password="Customerpass123!",
            username="customer",
            user_type="customer",
        )

        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Test Restaurant",
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00",
        )

    def test_owner_can_create_menu_item(self, api_client):
        api_client.force_authenticate(user=self.owner)

        url = reverse("menuitem-list")
        payload = {
            "name": "Pizza",
            "price": "200.00",
            "category": "main_course",
            "restaurant": str(self.restaurant.id),
            "preparation_time": 200,
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
            "preparation_time": 15,
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_cannot_add_item_to_other_restaurant(self, api_client):
        other_owner = User.objects.create_user(
            email="other1@test.com",
            password="Testpass123!",
            username="other",
            user_type="restaurant_owner",
        )

        other_restaurant = Restaurant.objects.create(
            owner=other_owner,
            name="Other Restaurant",
            email="other_restaurant@test.com",
            cuisine_type="indian",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00",
        )

        api_client.force_authenticate(user=self.owner)

        url = reverse("menuitem-list")
        payload = {
            "name": "Dish",
            "price": "150.00",
            "category": "main_course",
            "restaurant": str(other_restaurant.id),
            "preparation_time": 10,
        }

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_menu_items(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time=200,
        )

        url = reverse("menuitem-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 1

    def test_filter_menu_items_by_category(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time=200,
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Salad",
            price="80.00",
            category="appetizer",
            dietary_info="vegan",
            preparation_time=10,
        )

        url = reverse("menuitem-list") + "?category=main_course"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Pizza"

    def test_filter_menu_items_by_dietary_info(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            dietary_info="none",
            preparation_time=20,
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Vegan Bowl",
            price="150.00",
            category="main_course",
            dietary_info="vegan",
            preparation_time=15,
        )

        url = reverse("menuitem-list") + "?dietary_info=vegan"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Vegan Bowl"

    def test_search_menu_items(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Margherita Pizza",
            description="Classic cheese pizza",
            price="200.00",
            category="main_course",
            preparation_time=20,
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Burger",
            description="Beef burger",
            price="100.00",
            category="main_course",
            preparation_time=15,
        )

        url = reverse("menuitem-list") + "?search=pizza"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert "Pizza" in response.data["results"][0]["name"]

    def test_get_restaurant_menu_paginated(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time=20,
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Burger",
            price="100.00",
            category="main_course",
            preparation_time=15,
        )

        api_client.force_authenticate(user=self.customer)
        url = reverse("restaurant-menu", kwargs={"restaurant_id": self.restaurant.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        names = {item["name"] for item in response.data["results"]}
        assert names == {"Pizza", "Burger"}

    def test_restaurant_menu_filter_and_search(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Vegan Salad",
            description="Fresh greens",
            price="120.00",
            category="appetizer",
            dietary_info="vegan",
            preparation_time=10,
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Chicken Burger",
            description="Grilled chicken",
            price="180.00",
            category="main_course",
            dietary_info="none",
            preparation_time=20,
        )

        api_client.force_authenticate(user=self.customer)
        url = reverse(
            "restaurant-menu",
            kwargs={"restaurant_id": self.restaurant.id},
        )

        by_category = api_client.get(url, {"category": "appetizer"})
        assert by_category.status_code == status.HTTP_200_OK
        assert by_category.data["count"] == 1
        assert by_category.data["results"][0]["name"] == "Vegan Salad"

        by_diet = api_client.get(url, {"dietary_info": "vegan"})
        assert by_diet.status_code == status.HTTP_200_OK
        assert by_diet.data["count"] == 1

        by_search = api_client.get(url, {"search": "burger"})
        assert by_search.status_code == status.HTTP_200_OK
        assert by_search.data["count"] == 1
        assert by_search.data["results"][0]["name"] == "Chicken Burger"

    def test_get_restaurant_menu_not_found(self, api_client):
        api_client.force_authenticate(user=self.customer)
        url = reverse("restaurant-menu", kwargs={"restaurant_id": uuid.uuid4()})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Restaurant not found."

    def test_restaurant_menu_shows_new_items(self, api_client):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time=20,
        )

        api_client.force_authenticate(user=self.customer)
        url_menu = reverse(
            "restaurant-menu",
            kwargs={"restaurant_id": self.restaurant.id},
        )
        response = api_client.get(url_menu)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        api_client.force_authenticate(user=self.owner)
        response_create = api_client.post(
            reverse("menuitem-list"),
            {
                "name": "Burger",
                "price": "100.00",
                "category": "main_course",
                "restaurant": str(self.restaurant.id),
                "preparation_time": 15,
            },
        )
        assert response_create.status_code == status.HTTP_201_CREATED

        api_client.force_authenticate(user=self.customer)
        response_after = api_client.get(url_menu)
        assert response_after.status_code == status.HTTP_200_OK
        assert response_after.data["count"] == 2

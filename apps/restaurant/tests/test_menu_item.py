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
            "preparation_time": 200
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
            preparation_time=200
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
            preparation_time=200
        )

        url = reverse("menuitem-list") + "?category=main_course"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_get_restaurant_menu_success(self, api_client):
        # Create multiple menu items
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time=20
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Burger",
            price="100.00",
            category="main_course",
            preparation_time=15
        )

        api_client.force_authenticate(user=self.customer)
        url = reverse("restaurant-menu", kwargs={"restaurant_id": self.restaurant.id})
        response = api_client.get(url)

        # The response should not be paginated (so no 'results' key)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 2
        assert response.data[0]["name"] in ["Pizza", "Burger"]

    def test_get_restaurant_menu_not_found(self, api_client):
        import uuid
        api_client.force_authenticate(user=self.customer)
        url = reverse("restaurant-menu", kwargs={"restaurant_id": uuid.uuid4()})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Restaurant not found."

    def test_menu_item_cache_invalidation(self, api_client):
        # 1. Create initial menu item so the cache won't be empty
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price="200.00",
            category="main_course",
            preparation_time=20
        )

        # 2. Fetch menu (will cache the list containing Pizza)
        api_client.force_authenticate(user=self.customer)
        url_menu = reverse("restaurant-menu", kwargs={"restaurant_id": self.restaurant.id})
        response = api_client.get(url_menu)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        # 3. Add a second menu item (Burger)
        api_client.force_authenticate(user=self.owner)
        url_create = reverse("menuitem-list")
        payload = {
            "name": "Burger",
            "price": "100.00",
            "category": "main_course",
            "restaurant": str(self.restaurant.id),
            "preparation_time": 15
        }
        response_create = api_client.post(url_create, payload)
        assert response_create.status_code == status.HTTP_201_CREATED

        # 4. Fetch menu again (should return both Pizza and Burger as signal invalidates the cache)
        api_client.force_authenticate(user=self.customer)
        response_after = api_client.get(url_menu)
        assert response_after.status_code == status.HTTP_200_OK
        assert len(response_after.data) == 2
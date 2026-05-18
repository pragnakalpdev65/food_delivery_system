import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models.favorites import (
    FavoriteRestaurant,
    FavoriteMenuItem,
)
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem

User = get_user_model()

@pytest.fixture
def customer():
    return User.objects.create_user(
        email="customer@example.com",
        password="securepass123!",
        username="customer",
        first_name="Test",
        last_name="Customer",
        user_type="customer",
        is_verified=True,
    )


@pytest.fixture
def another_customer():
    return User.objects.create_user(
        email="another@example.com",
        password="securepass123!",
        username="anothercustomer",
        first_name="Another",
        last_name="Customer",
        user_type="customer",
        is_verified=True,
    )


@pytest.fixture
def auth_client(api_client, customer):
    refresh = RefreshToken.for_user(customer)

    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )

    return api_client


@pytest.fixture
def restaurant():
    owner = User.objects.create_user(
        email="owner@example.com",
        password="securepass123!",
        username="restaurantowner",
        user_type="restaurant_owner",
        is_verified=True,
    )

    return Restaurant.objects.create(
        owner=owner,
        name="Test Kitchen", 
        address="Surat",
        opening_time="10:00:00",
        closing_time="22:00:00",
    )


@pytest.fixture
def menu_item(restaurant):
    return MenuItem.objects.create(
        restaurant=restaurant,
        name="Paneer Pizza",
        description="Delicious Pizza",
        price=299,
        is_available=True,
        preparation_time= 20
    )


@pytest.fixture
def favorite_restaurant(customer, restaurant):
    return FavoriteRestaurant.objects.create(
        customer=customer,
        restaurant=restaurant,
    )


@pytest.fixture
def favorite_menu_item(customer, menu_item):
    return FavoriteMenuItem.objects.create(
        customer=customer,
        menu_item=menu_item,
    )

@pytest.mark.django_db
class TestFavoriteRestaurants:

    def test_customer_can_add_restaurant_to_favorites(self, auth_client, restaurant):
        url = reverse("favorite-restaurants-list")

        response = auth_client.post(
            url,
            {"restaurant_id": str(restaurant.id)},
            format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert FavoriteRestaurant.objects.filter(
            customer__email="customer@example.com",
            restaurant=restaurant,
        ).exists()

    def test_customer_cannot_add_duplicate_restaurant_favorite(self, auth_client, restaurant, favorite_restaurant):
        url = reverse("favorite-restaurants-list")

        response = auth_client.post(
            url,
            {"restaurant_id": str(restaurant.id)},
            format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in str(response.data).lower()

    def test_customer_can_remove_restaurant_from_favorites(self, auth_client, restaurant, favorite_restaurant):
        url = reverse(
            "favorite-restaurants-detail",
            kwargs={"pk": restaurant.id},
        )

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not FavoriteRestaurant.objects.filter(
            restaurant=restaurant
        ).exists()

    def test_customer_can_view_favorite_restaurants(self, auth_client, favorite_restaurant):
        url = reverse("favorite-restaurants-list")

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert len(response.data) >= 1  

    def test_favorite_restaurant_list_only_shows_current_user_data(self, auth_client, another_customer, restaurant, favorite_restaurant):
        FavoriteRestaurant.objects.create(
            customer=another_customer,
            restaurant=restaurant,
        )

        url = reverse("favorite-restaurants-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert len(response.data) == 1   
        assert response.data[0]["id"] == favorite_restaurant.id

    def test_check_restaurant_favorite_status_true(self, auth_client, restaurant, favorite_restaurant):
        url = reverse(
            "favorite-restaurants-check",
            kwargs={"pk": restaurant.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_favorited"] is True

    def test_check_restaurant_favorite_status_false(self, auth_client, restaurant):
        url = reverse(
            "favorite-restaurants-check",
            kwargs={"pk": restaurant.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_favorited"] is False

@pytest.mark.django_db
class TestFavoriteMenuItems:

    def test_customer_can_add_menu_item_to_favorites(self, auth_client, menu_item):
        url = reverse("favorite-menu-items-list")

        response = auth_client.post(
            url,
            {"item_id": menu_item.id},
            format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert FavoriteMenuItem.objects.filter(
            menu_item=menu_item
        ).exists()

    def test_customer_cannot_add_duplicate_menu_item_favorite(self, auth_client, menu_item, favorite_menu_item):
        url = reverse("favorite-menu-items-list")

        response = auth_client.post(
            url,
            {"item_id": menu_item.id},
            format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in str(response.data).lower()

    def test_customer_can_remove_menu_item_from_favorites(self, auth_client, menu_item, favorite_menu_item):
        url = reverse(
            "favorite-menu-items-detail",
            kwargs={"pk": menu_item.id},
        )

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not FavoriteMenuItem.objects.filter(
            menu_item=menu_item
        ).exists()

    def test_customer_can_view_favorite_menu_items(self, auth_client, favorite_menu_item):
        url = reverse("favorite-menu-items-list")

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # your view returns plain list (not paginated)
        assert len(response.data) >= 1

    def test_favorite_menu_items_only_for_current_user(self, auth_client, another_customer, menu_item, favorite_menu_item):
        FavoriteMenuItem.objects.create(
            customer=another_customer,
            menu_item=menu_item,
        )

        url = reverse("favorite-menu-items-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert len(response.data) == 1
        assert response.data[0]["id"] == favorite_menu_item.id

    def test_check_menu_item_favorite_status_true(self, auth_client, menu_item, favorite_menu_item):
        url = reverse(
            "favorite-menu-items-check",
            kwargs={"pk": menu_item.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_favorited"] is True

    def test_check_menu_item_favorite_status_false(self, auth_client, menu_item):
        url = reverse(
            "favorite-menu-items-check",
            kwargs={"pk": menu_item.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_favorited"] is False

    def test_add_menu_item_requires_item_id(self, auth_client):
        url = reverse("favorite-menu-items-list")

        response = auth_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "item_id" in response.data["detail"]
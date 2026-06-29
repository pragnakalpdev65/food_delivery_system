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
            user_type="restaurant_owner"
        )

        self.customer = User.objects.create_user(
            email="customer@test.com",
            password="Customerpass123!",
            username="customer",
            user_type="customer"
        )

    def test_create_restaurant_by_owner(self, api_client):
        api_client.force_authenticate(user=self.owner)

        url = reverse("restaurants-list")
        payload = {
            "name": "Test Restaurant",
            "cuisine_type": "indian",
            "email":"restaurant@test.com",
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
        assert len(response.data["results"]) == 1

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
        assert len(response.data["results"]) == 1

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
        assert len(response.data["results"]) == 1

    def test_get_restaurant_orders_all(self, api_client):
        from apps.order.models.order import Order
        
        # Create another restaurant for the same owner
        restaurant2 = Restaurant.objects.create(
            owner=self.owner,
            name="Second Restaurant",
            cuisine_type="indian",
            email="res2@test.com",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )
        
        # Create restaurant owned by self.owner
        restaurant1 = Restaurant.objects.create(
            owner=self.owner,
            name="First Restaurant",
            cuisine_type="indian",
            email="res1@test.com",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        Order.objects.create(customer=self.customer, restaurant=restaurant1, delivery_address="Surat")
        Order.objects.create(customer=self.customer, restaurant=restaurant2, delivery_address="Surat")

        api_client.force_authenticate(user=self.owner)
        url = reverse("restaurant-orders")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_get_restaurant_orders_filtered(self, api_client):
        from apps.order.models.order import Order
        
        restaurant1 = Restaurant.objects.create(
            owner=self.owner,
            name="First Restaurant",
            cuisine_type="indian",
            email="res1@test.com",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )
        restaurant2 = Restaurant.objects.create(
            owner=self.owner,
            name="Second Restaurant",
            cuisine_type="indian",
            email="res2@test.com",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        Order.objects.create(customer=self.customer, restaurant=restaurant1, delivery_address="Surat")
        Order.objects.create(customer=self.customer, restaurant=restaurant2, delivery_address="Surat")

        api_client.force_authenticate(user=self.owner)
        url = reverse("restaurant-orders") + f"?restaurant_id={restaurant1.id}"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["restaurant"] == restaurant1.id

    def test_get_restaurant_orders_other_owner(self, api_client):
        from apps.order.models.order import Order
        
        other_owner = User.objects.create_user(
            email="other_owner@test.com",
            password="Otherpass123!",
            username="other_owner",
            user_type="restaurant_owner"
        )
        other_restaurant = Restaurant.objects.create(
            owner=other_owner,
            name="Other Restaurant",
            cuisine_type="indian",
            email="otherres@test.com",
            address="Surat",
            opening_time="10:00:00",
            closing_time="22:00:00"
        )

        Order.objects.create(customer=self.customer, restaurant=other_restaurant, delivery_address="Surat")

        api_client.force_authenticate(user=self.owner)
        url = reverse("restaurant-orders") + f"?restaurant_id={other_restaurant.id}"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

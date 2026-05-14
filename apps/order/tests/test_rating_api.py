import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.restaurant.models import Restaurant

from apps.order.models.order import Order, OrderRating

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
def owner():    
    return User.objects.create_user(
                email="owner@test.com",
                password="Testpass123!",
                username="owner",
                user_type="restaurant_owner"
            )

@pytest.fixture
def restaurant(db,owner):
    return Restaurant.objects.create(
        owner=owner,
        name="Test Kitchen", 
        address="Surat",
        opening_time="10:00:00",
        closing_time="22:00:00")

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
def delivered_order(customer,restaurant):
    return Order.objects.create(
        customer=customer,
        restaurant = restaurant,
        status="DELIVERED",
        actual_delivery_time=timezone.now() - timedelta(days=1),
        total_amount=500,
    )


@pytest.fixture
def pending_order(customer,restaurant):
    return Order.objects.create(
        customer=customer,
        restaurant = restaurant,
        status="PENDING",
        total_amount=300,
    )


@pytest.fixture
def expired_order(customer,restaurant):
    return Order.objects.create(
        customer=customer,
        restaurant = restaurant,
        status="DELIVERED",
        actual_delivery_time=timezone.now() - timedelta(days=8),
        total_amount=700,
    )


@pytest.fixture
def order_rating(customer, delivered_order):
    return OrderRating.objects.create(
        order=delivered_order,
        customer=customer,
        food_quality=5,
        delivery_speed=4,
        packaging_quality=5,
        overall_rating=4.7,
        comment="Very good service",
        would_recommend=True,
        had_issues=False,
    )

@pytest.mark.django_db
class TestCreateOrderRating:

    def test_customer_can_submit_rating(self, auth_client, delivered_order):
        """Customer should be able to rate delivered order."""
        url = reverse(
            "create-order-rating",
            kwargs={"order_id": delivered_order.id},
        ) # delivered_at

        payload = {
            "food_quality": 5,
            "delivery_speed": 4,
            "packaging_quality": 5,
            "comment": "Excellent food",
            "would_recommend": True,
            "had_issues": False,
        }

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        assert response.data["food_quality"] == 5
        assert response.data["delivery_speed"] == 4
        assert response.data["packaging_quality"] == 5

        expected_average = round((5 + 4 + 5) / 3)

        assert response.data["overall_rating"] == expected_average

    def test_cannot_rate_non_delivered_order(self, auth_client, pending_order):
        """Rating should fail if order not delivered."""

        url = reverse(
            "create-order-rating",
            kwargs={"order_id": pending_order.id},
        )

        payload = {
            "food_quality": 5,
            "delivery_speed": 5,
            "packaging_quality": 5,
        }

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "delivered" in str(response.data).lower()

    def test_cannot_rate_after_7_days(self, auth_client, expired_order):
        """Rating should fail after allowed 7 day window."""

        url = reverse(
            "create-order-rating",
            kwargs={"order_id": expired_order.id},
        )

        payload = {
            "food_quality": 4,
            "delivery_speed": 4,
            "packaging_quality": 4,
        }

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Rating period expired." in response.data["errors"]["non_field_errors"]

    def test_customer_cannot_rate_other_customer_order(self,auth_client,another_customer,restaurant):
        """Customer cannot rate someone else's order."""

        order = Order.objects.create(
            customer=another_customer,
            restaurant=restaurant,
            status="DELIVERED",
            actual_delivery_time=timezone.now(),
            total_amount=400,
        )

        url = reverse(
            "create-order-rating",
            kwargs={"order_id": order.id},
        )

        payload = {
            "food_quality": 5,
            "delivery_speed": 5,
            "packaging_quality": 5,
        }

        response = auth_client.post(url, payload, format="json")

        assert "You can only rate your own orders." in response.data["errors"]["non_field_errors"]
        
    def test_customer_cannot_submit_duplicate_rating(self,auth_client,delivered_order,order_rating):
        """Order can only be rated once."""

        url = reverse(
            "create-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        payload = {
            "food_quality": 5,
            "delivery_speed": 5,
            "packaging_quality": 5,
        }

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in str(response.data).lower()

@pytest.mark.django_db
class TestGetOrderRating:

    def test_customer_can_get_order_rating(self,auth_client,delivered_order,order_rating):
        """Customer should retrieve their order rating."""

        url = reverse(
            "get-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["comment"] == "Very good service"

    def test_get_rating_not_found(self,auth_client,delivered_order):
        """Should return 404 if rating does not exist."""

        url = reverse(
            "get-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestUpdateOrderRating:

    def test_customer_can_update_rating_within_24_hours(self,auth_client,delivered_order,order_rating):
        """Customer can update rating within 24 hours."""

        url = reverse(
            "update-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        payload = {
            "order": str(delivered_order.id),
            "food_quality": 3,
            "delivery_speed": 4,
            "packaging_quality": 3,
            "comment": "Updated review",
        }

        response = auth_client.put(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        order_rating.refresh_from_db()

        assert order_rating.food_quality == 3
        assert order_rating.comment == "Updated review"

    def test_customer_cannot_update_after_24_hours(self,auth_client,delivered_order,order_rating):
        """Update should fail after 24 hours."""

        order_rating.created_at = timezone.now() - timedelta(days=2)
        order_rating.save()

        url = reverse(
            "update-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        payload = {
            "order": str(delivered_order.id),
            "food_quality": 2,
            "delivery_speed": 2,
            "packaging_quality": 2,
        }

        response = auth_client.put(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "24 hours" in str(response.data).lower()

@pytest.mark.django_db
class TestRatingHistory:

    def test_customer_can_view_rating_history(
        self,
        auth_client,
        order_rating,
    ):
        """Customer should see all submitted ratings."""

        url = reverse("my-ratings")

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert len(response.data) >= 1

    def test_rating_history_only_shows_customer_ratings(self,auth_client,another_customer,restaurant):
        """Users should only see their own ratings."""

        order = Order.objects.create(
            customer=another_customer,
            restaurant=restaurant,
            status="DELIVERED",
            actual_delivery_time=timezone.now(),
            total_amount=200,
        )

        OrderRating.objects.create(
            order=order,
            customer=another_customer,
            food_quality=5,
            delivery_speed=5,
            packaging_quality=5,
            overall_rating=5,
        )

        url = reverse("my-ratings")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
         
        assert len(response.data["results"]) == 0
        
        for rating in response.data["results"]:
            assert rating["customer"] != another_customer.id

@pytest.mark.django_db
class TestOrderRatingValidation:

    @pytest.mark.parametrize(
        "field,value",
        [
            ("food_quality", 0),
            ("food_quality", 6),
            ("delivery_speed", 0),
            ("delivery_speed", 10),
            ("packaging_quality", -1),
            ("packaging_quality", 7),
        ],
    )
    def test_rating_fields_must_be_between_1_and_5(self,auth_client,delivered_order,field,value):
        """All rating values must stay between 1 and 5."""

        url = reverse(
            "create-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        payload = {
            "food_quality": 5,
            "delivery_speed": 5,
            "packaging_quality": 5,
        }

        payload[field] = value

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_issue_description_required_when_had_issues_true(self,auth_client,delivered_order,):
        """Issue description required when had_issues=True."""

        url = reverse(
            "create-order-rating",
            kwargs={"order_id": delivered_order.id},
        )

        payload = {
            "food_quality": 2,
            "delivery_speed": 2,
            "packaging_quality": 2,
            "had_issues": True,
        }

        response = auth_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "issue_description" in response.data["errors"]
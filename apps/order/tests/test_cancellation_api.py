import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.order.models.order import Order
from apps.order.models.cancellation import (
    CancellationPolicy,
    OrderCancellation,
)
from apps.restaurant.models.restaurant import Restaurant
from apps.core.constants.choices import OrderStatus
from apps.core.constants.choices import UserType
User = get_user_model()

@pytest.fixture
def customer():
    return User.objects.create_user(
        email="customer@test.com",
        password="pass1234",
        username="customer",
        user_type="customer",
        is_verified=True,
    )


@pytest.fixture
def owner():
    return User.objects.create_user(
        email="owner@test.com",
        password="pass1234",
        username="owner",
        user_type="restaurant_owner",
        is_verified=True,
    )

@pytest.fixture
def driver(db):
    return User.objects.create_user(
        username="driver",
        email="driver@example.com",    
        password="pass123",
        user_type=UserType.DELIVERY_DRIVER
    )
@pytest.fixture
def auth_client(api_client, customer):
    refresh = RefreshToken.for_user(customer)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )
    return api_client


@pytest.fixture
def owner_client(api_client, owner):
    refresh = RefreshToken.for_user(owner)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )
    return api_client

@pytest.fixture
def driver_client(api_client, owner):
    refresh = RefreshToken.for_user(owner)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )
    return api_client

@pytest.fixture
def restaurant(owner):
    return Restaurant.objects.create(
        owner=owner,
        name="Test Restaurant",
        address="Test Address",
        opening_time="10:00:00",
        closing_time="22:00:00",
    )


@pytest.fixture
def cancellation_policy(restaurant):
    return CancellationPolicy.objects.create(
        restaurant=restaurant,
        full_refund_window=5,
        partial_refund_window=15,
        partial_refund_percentage=50,
        allow_customer_cancellation=True,
    )


@pytest.fixture
def order(customer, restaurant):
    return Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        total_amount=1000,
        status="placed",
        created_at=timezone.now(),
    )



@pytest.mark.django_db
class TestOrderCancellation:

    def test_full_refund_within_window(self, auth_client, order, cancellation_policy):
        """Full refund if cancelled within full window."""

        order.created_at = timezone.now() - timedelta(minutes=3)
        order.save()

        url = reverse("order-cancel", kwargs={"order_id": order.id})

        response = auth_client.post(
            url,
            {"reason": "customer_request"},
        )
        assert response.status_code == status.HTTP_200_OK

        assert response.data["refund_percentage"] == 100
        assert response.data["refund_amount"] == 1000

        assert OrderCancellation.objects.filter(order=order).exists()

    def test_partial_refund_within_window(self, auth_client, order, cancellation_policy):
        """Partial refund within second window."""

        order.created_at = timezone.now() - timedelta(minutes=10)
        order.save()

        url = reverse("order-cancel", kwargs={"order_id": order.id})

        response = auth_client.post(
            url,
            {"reason": "customer_request"},
        )

        assert response.status_code == status.HTTP_200_OK

        assert response.data["refund_percentage"] == 50
        assert response.data["refund_amount"] == 500
        
    def test_no_refund_after_window(self, auth_client, order, cancellation_policy):
            """No refund after windows expire."""

            order.created_at = timezone.now() - timedelta(minutes=20)
            order.save()

            url = reverse("order-cancel", kwargs={"order_id": order.id})

            response = auth_client.post(
                url,
                {"reason": "customer_request"},
            )

            assert response.status_code == status.HTTP_200_OK

            assert response.data["refund_percentage"] == 0
            assert response.data["refund_amount"] == 0

    def test_cancellation_requires_reason(self, auth_client, order, cancellation_policy):
            """Reason is required."""

            url = reverse("order-cancel", kwargs={"order_id": order.id})

            response = auth_client.post(url, {})

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "reason" in response.data["error"]

    def test_user_cannot_cancel_others_order(self, api_client, order, cancellation_policy):
            """Users cannot cancel someone else's order."""

            another_user = User.objects.create_user(
                email="other@test.com",
                password="pass1234",
                user_type="customer",
                is_verified=True,
                username="testuser",
            )

            refresh = RefreshToken.for_user(another_user)
            api_client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
            )

            url = reverse("order-cancel", kwargs={"order_id": order.id})

            response = api_client.post(
                url,
                {"reason": "customer_request"},
            )
            assert "Not allowed" in response.data["error"]

    def test_cannot_cancel_if_disabled(self, auth_client, order, cancellation_policy):
            """Cancellation disabled by restaurant."""

            cancellation_policy.allow_customer_cancellation = False
            cancellation_policy.save()

            url = reverse("order-cancel", kwargs={"order_id": order.id})

            response = auth_client.post(
                url,
                {"reason": "customer_request"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_cancel_twice(self, auth_client, order, cancellation_policy):
            """Order cannot be cancelled twice."""

            OrderCancellation.objects.create(
                order=order,
                refund_amount=0,
                refund_percentage=0,
            )

            url = reverse("order-cancel", kwargs={"order_id": order.id})

            response = auth_client.post(
                url,
                {"reason": "customer_request"},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
    def test_cannot_cancel_after_preparing(self, auth_client, order, client):
            order.status = OrderStatus.PREPARING
            order.save()

            url = reverse('order-cancel', args=[order.id])
            response = auth_client.post(url,{"reason": "customer_request"},)
            assert response.data["error"] ==  "Order cannot be cancelled at this stage"
            
    def test_driver_cannot_cancel_order(self, driver_client, order, client):

            url = reverse('order-cancel', args=[order.id])
            response = driver_client.post(url,{"reason": "customer_request"},)
            assert response.status_code == 403

    def test_customer_can_cancel_pending_order(self, auth_client, order, client):

            url = reverse('order-cancel', args=[order.id])

            response = auth_client.post(url,{"reason": "customer_request"})
            assert response.status_code == 200
            order.refresh_from_db()
            assert order.status == OrderStatus.CANCELLED

@pytest.mark.django_db
class TestCancellationPolicy:

    def test_owner_can_update_policy(self, owner_client, restaurant, cancellation_policy):
        """Owner should update policy."""

        url = reverse(
            "cancellation-policy",
            kwargs={"restaurant_id": restaurant.id},
        )

        data = {
            "full_refund_window": 10,
            "partial_refund_window": 20,
            "partial_refund_percentage": 30,
        }

        response = owner_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK

        cancellation_policy.refresh_from_db()

        assert cancellation_policy.full_refund_window == 10
        assert cancellation_policy.partial_refund_percentage == 30

    def test_non_owner_cannot_update_policy(self, auth_client, restaurant, cancellation_policy):
        """Non-owner should not update policy."""

        url = reverse(
            "cancellation-policy",
            kwargs={"restaurant_id": restaurant.id},
        )

        response = auth_client.put(url, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestCancellationInfo:

    def test_get_cancellation_info(self, auth_client, order, cancellation_policy):
        """User can view cancellation eligibility."""

        url = reverse(
            "cancellation-info",
            kwargs={"order_id": order.id},
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        assert "can_cancel" in response.data
        assert "refund_percentage" in response.data
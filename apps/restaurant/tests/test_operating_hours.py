import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import time, timedelta

from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.operating_hours import (
    OperatingHours,
    SpecialHours
)

User = get_user_model()



@pytest.fixture
def owner():
    return User.objects.create_user(
        email="owner@example.com",
        password="securepass123!",
        username="owner",
        user_type="restaurant_owner",
        is_verified=True,
    )


@pytest.fixture
def auth_client(api_client, owner):
    refresh = RefreshToken.for_user(owner)

    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
    )
    return api_client


@pytest.fixture
def restaurant(owner):
    return Restaurant.objects.create(
        owner=owner,
        name="Test Kitchen",
        address="Surat",
        opening_time="10:00:00",
        closing_time="22:00:00",
    )
    
    
    
@pytest.mark.django_db
class TestOperatingHours:

    def test_owner_can_create_operating_hours(self, auth_client, restaurant):
        url = reverse(
            "operating-hours",
            kwargs={"pk": restaurant.id}
        )

        data = {
            "day_of_week": 1,
            "opening_time": "10:00:00",
            "closing_time": "22:00:00",
            "is_closed": False,
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        assert OperatingHours.objects.filter(
            restaurant=restaurant,
            day_of_week=1
        ).exists()

    def test_owner_can_get_operating_hours(self, auth_client, restaurant):
        OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=1,
            opening_time="10:00:00",
            closing_time="22:00:00",
        )

        url = reverse(
            "operating-hours",
            kwargs={"pk": restaurant.id}
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_owner_can_update_operating_hours(self, auth_client, restaurant):
        OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=1,
            opening_time="10:00:00",
            closing_time="22:00:00",
        )

        url = reverse(
            "operating-hours-update",
            kwargs={"pk": restaurant.id, "day": 1}
        )

        data = {
            "opening_time": "11:00:00",
            "day_of_week":1,
            "closing_time":"17:00:00"
        }

        response = auth_client.put(url, data)

        assert response.status_code == status.HTTP_200_OK

        obj = OperatingHours.objects.get(
            restaurant=restaurant,
            day_of_week=1
        )

        assert str(obj.opening_time) == "11:00:00"    
        
@pytest.mark.django_db
class TestSpecialHours:

    def test_owner_can_add_special_hours(self, auth_client, restaurant):
        url = reverse(
            "special-hours",
            kwargs={"pk": restaurant.id}
        )

        data = {
            "date": str(timezone.localdate()),
            "opening_time": "12:00:00",
            "closing_time": "20:00:00",
            "reason": "Holiday hours"
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        assert SpecialHours.objects.filter(
            restaurant=restaurant
        ).exists()

    def test_owner_can_list_special_hours(self, auth_client, restaurant):
        SpecialHours.objects.create(
            restaurant=restaurant,
            date=timezone.localdate(),
            opening_time="12:00:00",
            closing_time="20:00:00",
            reason="Test"
        )

        url = reverse(
            "special-hours",
            kwargs={"pk": restaurant.id}
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_owner_can_delete_special_hours(self, auth_client, restaurant):
        special = SpecialHours.objects.create(
            restaurant=restaurant,
            date=timezone.localdate(),
            opening_time="12:00:00",
            closing_time="20:00:00",
            reason="Test"
        )

        url = reverse(
            "special-hours-delete",
            kwargs={
                "pk": restaurant.id,
                "special_hours_id": special.id
            }
        )

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not SpecialHours.objects.filter(
            id=special.id
        ).exists()
        
@pytest.mark.django_db
class TestRestaurantAvailability:

    def test_is_open_true(self, auth_client, restaurant):
        now = timezone.localtime().time()

        OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=timezone.localdate().weekday(),
            opening_time=(now.replace(hour=0, minute=0)),
            closing_time=(now.replace(hour=23, minute=59)),
        )

        url = reverse(
            "restaurant-is-open",
            kwargs={"pk": restaurant.id}
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_open"] is True

    def test_is_open_false_when_closed(self, auth_client, restaurant):
        OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=timezone.localdate().weekday(),
            opening_time=time(1, 0),
            closing_time=time(2, 0),
        )

        url = reverse(
            "restaurant-is-open",
            kwargs={"pk": restaurant.id}
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_open"] is False

    def test_special_hours_override(self, auth_client, restaurant):
        today = timezone.localdate()

        OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=today.weekday(),
            opening_time=time(10, 0),
            closing_time=time(22, 0),
        )

        SpecialHours.objects.create(
            restaurant=restaurant,
            date=today,
            is_closed=True,
            reason="Holiday"
        )

        url = reverse(
            "restaurant-is-open",
            kwargs={"pk": restaurant.id}
        )

        response = auth_client.get(url)

        assert response.data["is_open"] is False
        
@pytest.mark.django_db
class TestNextOpening:

    def test_get_next_opening_time(self, auth_client, restaurant):
        tomorrow = timezone.localdate() + timedelta(days=1)

        OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=tomorrow.weekday(),
            opening_time=time(10, 0),
            closing_time=time(22, 0),
        )

        url = reverse(
            "restaurant-next-opening",
            kwargs={"pk": restaurant.id}
        )

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["next_opening_time"] is not None
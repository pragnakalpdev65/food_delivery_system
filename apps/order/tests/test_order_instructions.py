import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from apps.order.models.order import Order
from apps.order.models.instruction_templates import InstructionTemplate
from apps.core.constants.choices import UserType
from apps.users.models.user import CustomUser
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem
from apps.core.constants.choices import OrderStatus
from apps.restaurant.models.operating_hours import OperatingHours

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def customer(db):
    return CustomUser.objects.create_user(
        username="customer",
        email="customer@example.com",  
        password="pass123",
        user_type=UserType.CUSTOMER
    )

@pytest.fixture
def owner(db):
    return CustomUser.objects.create_user(
        username="owner",
        email="owner@example.com",     
        password="pass123",
        user_type=UserType.RESTAURANT_OWNER
    )

@pytest.fixture
def driver(db):
    return CustomUser.objects.create_user(
        username="driver",
        email="driver@example.com",    
        password="pass123",
        user_type=UserType.DELIVERY_DRIVER
    )

@pytest.fixture
def restaurant(db, owner):
    return Restaurant.objects.create(
        owner=owner,
        name="Test Restaurant",
        delivery_fee=50,
        opening_time = "10:00:00",
        closing_time = "20:00:00",
        is_open = True
    )
@pytest.fixture
def operating_hours(db,restaurant):
    return OperatingHours.objects.create(
            restaurant=restaurant,
            day_of_week=0,
            opening_time="10:00:00",
            closing_time="22:00:00",
        )

@pytest.fixture
def menu_item(db, restaurant):
    return MenuItem.objects.create(
        restaurant=restaurant,
        name="Burger",
        price=100,
        preparation_time="300"
    )


@pytest.fixture
def order(db, customer, restaurant):
    return Order.objects.create(
        customer=customer,
        restaurant=restaurant,
        delivery_address="Test Address",
        status=OrderStatus.PENDING
    )

@pytest.mark.django_db
def test_delivery_instructions_exceed_limit(customer, restaurant, menu_item, client):
    client.force_authenticate(user=customer)

    url = reverse("orders-list")

    payload = {
        "restaurant": restaurant.id,
        "delivery_address": "Test Address",
        "delivery_instructions": "A" * 501,  # exceed limit
        "items": [
            {
                "menu_item": menu_item.id,
                "quantity": 1
            }
        ]
    }

    response = client.post(url, payload, format="json")
    assert response.status_code == 400
    assert "delivery_instructions" in response.data["errors"]
    
@pytest.mark.django_db
def test_item_special_instructions_exceed_limit(customer, restaurant, menu_item, client):
    client.force_authenticate(user=customer)

    url = reverse("orders-list")

    payload = {
        "restaurant": restaurant.id,
        "delivery_address": "Test Address",
        "items": [
            {
                "menu_item": menu_item.id,
                "quantity": 1,
                "special_instructions": "A" * 201
            }
        ]
    }

    response = client.post(url, payload, format="json")

    assert response.status_code == 400

    
@pytest.mark.django_db
def test_get_instruction_templates(client,customer):
    client.force_authenticate(user=customer)

    InstructionTemplate.objects.create(
        category="delivery",
        text="Leave at door",
        is_active=True
    )

    InstructionTemplate.objects.create(
        category="delivery",
        text="Old template",
        is_active=False
    )

    url = reverse("instruction-templates")

    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["text"] == "Leave at door"
    
@pytest.mark.django_db
def test_templates_grouped_by_category(client,customer):
    client.force_authenticate(user=customer)
    
    InstructionTemplate.objects.create(category="delivery", text="Call me")
    InstructionTemplate.objects.create(category="food", text="Extra spicy")
    InstructionTemplate.objects.create(category="packaging", text="No plastic")

    url = reverse("instruction-templates")
    response = client.get(url)

    categories = [item["category"] for item in response.data]

    assert "delivery" in categories
    assert "food" in categories
    assert "packaging" in categories
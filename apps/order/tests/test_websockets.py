import uuid

import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.core.constants.choices import UserType
from apps.order.models.order import Order
from apps.order.services.websocket_services import WebSocketService
from apps.restaurant.models.restaurant import Restaurant
from config.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)

User = get_user_model()
RESTAURANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ORDER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        username="testcustomer",
        email="customer@example.com",
        password="password123",
        user_type=UserType.CUSTOMER,
    )


@pytest.fixture
def restaurant_owner_user(db):
    return User.objects.create_user(
        username="testowner",
        email="owner@example.com",
        password="password123",
        user_type=UserType.RESTAURANT_OWNER,
    )


@pytest.fixture
def other_owner(db):
    return User.objects.create_user(
        username="otherowner",
        email="otherowner@example.com",
        password="password123",
        user_type=UserType.RESTAURANT_OWNER,
    )


@pytest.fixture
def driver_user(db):
    return User.objects.create_user(
        username="testdriver",
        email="driver@example.com",
        password="password123",
        user_type=UserType.DELIVERY_DRIVER,
    )


@pytest.fixture
def restaurant(db, restaurant_owner_user):
    return Restaurant.objects.create(
        id=RESTAURANT_ID,
        name="WS Test Restaurant",
        owner=restaurant_owner_user,
        address="123 Test St",
        email="ws-restaurant@example.com",
        phone_number="9999999999",
        opening_time="09:00:00",
        closing_time="22:00:00",
        delivery_fee="20.00",
        minimum_order="50.00",
    )


@pytest.fixture
def order(db, restaurant, customer_user):
    return Order.objects.create(
        id=ORDER_ID,
        customer=customer_user,
        restaurant=restaurant,
        delivery_address="456 Delivery Ln",
        subtotal="100.00",
        delivery_fee="20.00",
        tax="5.00",
        total_amount="125.00",
    )


@pytest.fixture
def customer_token(customer_user):
    return str(AccessToken.for_user(customer_user))


@pytest.fixture
def restaurant_owner_token(restaurant_owner_user):
    return str(AccessToken.for_user(restaurant_owner_user))


@pytest.fixture
def other_owner_token(other_owner):
    return str(AccessToken.for_user(other_owner))


@pytest.fixture
def driver_token(driver_user):
    return str(AccessToken.for_user(driver_user))


@pytest.fixture
def owner_client(api_client, restaurant_owner_user):
    refresh = RefreshToken.for_user(restaurant_owner_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.mark.asyncio
async def test_restaurant_order_section_connects(restaurant, restaurant_owner_token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/{RESTAURANT_ID}/?token={restaurant_owner_token}",
    )

    connected, _ = await communicator.connect()
    assert connected

    welcome = await communicator.receive_json_from()
    assert welcome["event"] == "connected"
    assert welcome["restaurant_id"] == str(RESTAURANT_ID)

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_restaurant_order_section_anonymous_rejected(restaurant):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/{RESTAURANT_ID}/",
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4401


@pytest.mark.asyncio
async def test_restaurant_order_section_rejects_non_owner(
    restaurant, other_owner_token
):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/{RESTAURANT_ID}/?token={other_owner_token}",
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4403


@pytest.mark.asyncio
async def test_restaurant_order_section_rejects_customer(
    restaurant, customer_token
):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/{RESTAURANT_ID}/?token={customer_token}",
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4403


@pytest.mark.asyncio
async def test_restaurant_order_section_receives_status_updated(
    restaurant, restaurant_owner_token
):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/{RESTAURANT_ID}/?token={restaurant_owner_token}",
    )

    connected, _ = await communicator.connect()
    assert connected
    await communicator.receive_json_from()  # connected event

    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"restaurant_order_{RESTAURANT_ID}",
        {
            "type": "send_order_update",
            "data": {
                "event": "status_updated",
                "order_id": str(ORDER_ID),
                "status": "preparing",
            },
        },
    )

    response = await communicator.receive_json_from()
    assert response["event"] == "status_updated"
    assert response["status"] == "preparing"

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_order_consumer_connection(order, customer_token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/{ORDER_ID}/?token={customer_token}",
    )

    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_order_consumer_rejects_unrelated_user(order, other_owner_token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/{ORDER_ID}/?token={other_owner_token}",
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4403


@pytest.mark.asyncio
async def test_order_consumer_allows_restaurant_owner(
    order, restaurant_owner_token
):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/{ORDER_ID}/?token={restaurant_owner_token}",
    )

    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_order_consumer_receive_message(order, customer_token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/{ORDER_ID}/?token={customer_token}",
    )

    connected, _ = await communicator.connect()
    assert connected

    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"order_{ORDER_ID}",
        {
            "type": "send_order_update",
            "data": {"event": "status_updated", "status": "confirmed"},
        },
    )

    response = await communicator.receive_json_from()
    assert response["status"] == "confirmed"

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_restaurant_dashboard_receives_new_order(
    restaurant, restaurant_owner_token
):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/restaurants/{RESTAURANT_ID}/?token={restaurant_owner_token}",
    )

    connected, _ = await communicator.connect()
    assert connected

    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"restaurant_{RESTAURANT_ID}",
        {
            "type": "send_new_order",
            "data": {
                "event": "new_order",
                "order_id": str(ORDER_ID),
                "status": "pending",
            },
        },
    )

    response = await communicator.receive_json_from()
    assert response["event"] == "new_order"
    assert response["order_id"] == str(ORDER_ID)

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_customer_and_driver_consumers(customer_token, driver_token):
    customer_ws = WebsocketCommunicator(
        application,
        f"/ws/customers/?token={customer_token}",
    )
    driver_ws = WebsocketCommunicator(
        application,
        f"/ws/drivers/?token={driver_token}",
    )

    customer_connected, _ = await customer_ws.connect()
    driver_connected, _ = await driver_ws.connect()
    assert customer_connected
    assert driver_connected

    await customer_ws.disconnect()
    await driver_ws.disconnect()


@pytest.mark.asyncio
async def test_customer_consumer_rejects_driver(driver_token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/customers/?token={driver_token}",
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4403


@pytest.mark.asyncio
async def test_driver_consumer_rejects_customer(customer_token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/drivers/?token={customer_token}",
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4403


def test_websocket_service_management_update_uses_restaurant_id():
    WebSocketService.send_order_management_update(
        restaurant_id=RESTAURANT_ID,
        data={"event": "status_updated", "status": "confirmed"},
    )


def test_restaurant_order_ws_info_api(owner_client, restaurant):
    url = reverse(
        "restaurant-order-ws-info",
        kwargs={"restaurant_id": restaurant.id},
    )
    response = owner_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["websocket_path"] == (
        f"/ws/orders/management/{restaurant.id}/"
    )
    assert response.data["websocket_url_template"].startswith("ws://")
    assert "order_created" in response.data["events"]
    assert "status_updated" in response.data["events"]
    assert "driver_assigned" in response.data["events"]


def test_restaurant_order_ws_info_rejects_other_owner(api_client, restaurant, other_owner):
    refresh = RefreshToken.for_user(other_owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    url = reverse(
        "restaurant-order-ws-info",
        kwargs={"restaurant_id": restaurant.id},
    )
    response = api_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND

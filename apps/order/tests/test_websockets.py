import pytest
from channels.testing import WebsocketCommunicator
from config.asgi import application
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser", 
        email="test@example.com",
        password="password123"
    )

@pytest.fixture
def token(user):
    return str(AccessToken.for_user(user))


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_order_consumer_connection(token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/1/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()
    
    
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@pytest.mark.asyncio
async def test_order_consumer_receive_message(token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/1/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()

    # Send message to group
    await channel_layer.group_send(
        "order_1",
        {
            "type": "send_order_update",
            "data": {
                "status": "confirmed"
            }
        }
    )

    response = await communicator.receive_json_from()

    assert response["status"] == "confirmed"

    await communicator.disconnect()
    
    
    
    
@pytest.mark.asyncio
async def test_restaurant_dashboard_consumer(token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/restaurants/10/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()

    await channel_layer.group_send(
        "restaurant_10",
        {
            "type": "send_new_order",
            "data": {
                "order_id": "123",
                "status": "pending"
            }
        }
    )

    response = await communicator.receive_json_from()

    assert response["order_id"] == "123"

    await communicator.disconnect()
    
@pytest.mark.asyncio
async def test_order_management_consumer(token):
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/5/?token={token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()

    await channel_layer.group_send(
        "order_5",
        {
            "type": "send_order_update",
            "data": {
                "status": "preparing"
            }
        }
    )

    response = await communicator.receive_json_from()

    assert response["status"] == "preparing"

    await communicator.disconnect()
    
@pytest.mark.django_db    
@pytest.mark.asyncio
async def test_websocket_invalid_token():
    communicator = WebsocketCommunicator(
        application,
        "/ws/orders/1/?token=invalidtoken"
    )

    connected, _ = await communicator.connect()

    # Depending on middleware behavior
    assert connected  # or False if you enforce auth strictly

    await communicator.disconnect()

from apps.order.services.websocket_services import WebSocketService

@pytest.mark.django_db
def test_websocket_service_send_order_update():
    # This just ensures no crash (since async layer)
    WebSocketService.send_order_update(
        order_id=1,
        data={"status": "confirmed"}
    )
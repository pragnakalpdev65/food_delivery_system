import pytest
from channels.testing import WebsocketCommunicator
from config.asgi import application
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from apps.core.constants.choices import UserType

pytestmark = pytest.mark.django_db(transaction=True)

User = get_user_model()

@pytest.fixture
def customer_user(db):
    return User.objects.create_user(
        username="testcustomer", 
        email="customer@example.com",
        password="password123",
        user_type=UserType.CUSTOMER
    )

@pytest.fixture
def restaurant_owner_user(db):
    return User.objects.create_user(
        username="testowner", 
        email="owner@example.com",
        password="password123",
        user_type=UserType.RESTAURANT_OWNER
    )

@pytest.fixture
def driver_user(db):
    return User.objects.create_user(
        username="testdriver", 
        email="driver@example.com",
        password="password123",
        user_type=UserType.DELIVERY_DRIVER
    )

@pytest.fixture
def customer_token(customer_user):
    return str(AccessToken.for_user(customer_user))

@pytest.fixture
def restaurant_owner_token(restaurant_owner_user):
    return str(AccessToken.for_user(restaurant_owner_user))

@pytest.fixture
def driver_token(driver_user):
    return str(AccessToken.for_user(driver_user))


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_order_consumer_connection(customer_token):
    """Test that authenticated customer can connect to OrderConsumer."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/1/?token={customer_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_order_consumer_anonymous_rejected():
    """Test that anonymous user is rejected from OrderConsumer."""
    communicator = WebsocketCommunicator(
        application,
        "/ws/orders/1/"
    )

    connected, code = await communicator.connect()
    # Should be rejected with 4401 Unauthorized
    assert not connected or code == 4401


@pytest.mark.asyncio
async def test_order_consumer_receive_message(customer_token):
    """Test that OrderConsumer receives order update messages."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/1/?token={customer_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    from channels.layers import get_channel_layer
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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_order_management_consumer_connection(restaurant_owner_token):
    """Test that authenticated restaurant owner can connect to OrderManagementConsumer."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/5/?token={restaurant_owner_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_order_management_consumer_anonymous_rejected():
    """Test that anonymous user is rejected from OrderManagementConsumer."""
    communicator = WebsocketCommunicator(
        application,
        "/ws/orders/management/5/"
    )

    connected, code = await communicator.connect()
    # Should be rejected with 4401 Unauthorized
    assert not connected or code == 4401


@pytest.mark.asyncio
async def test_order_management_consumer_receive_message(restaurant_owner_token):
    """Test that OrderManagementConsumer receives order update messages from correct group."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/orders/management/5/?token={restaurant_owner_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()

    # Send message to the CORRECT group for OrderManagementConsumer
    await channel_layer.group_send(
        "restaurant_order_5",
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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_restaurant_dashboard_consumer_connection(restaurant_owner_token):
    """Test that authenticated restaurant owner can connect to RestaurantDashboardConsumer."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/restaurants/10/?token={restaurant_owner_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_restaurant_dashboard_consumer_anonymous_rejected():
    """Test that anonymous user is rejected from RestaurantDashboardConsumer."""
    communicator = WebsocketCommunicator(
        application,
        "/ws/restaurants/10/"
    )

    connected, code = await communicator.connect()
    assert not connected or code == 4401

    
@pytest.mark.asyncio
async def test_restaurant_dashboard_consumer_receive_message(restaurant_owner_token):
    """Test that RestaurantDashboardConsumer receives new order messages."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/restaurants/10/?token={restaurant_owner_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    from channels.layers import get_channel_layer
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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_customer_consumer_connection(customer_token):
    """Test that authenticated customer can connect to CustomerConsumer."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/customers/?token={customer_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_customer_consumer_anonymous_rejected():
    """Test that anonymous user is rejected from CustomerConsumer."""
    communicator = WebsocketCommunicator(
        application,
        "/ws/customers/"
    )

    connected, code = await communicator.connect()
    # Should be rejected with 4401 Unauthorized
    assert not connected or code == 4401


@pytest.mark.asyncio
async def test_driver_consumer_connection(driver_token):
    """Test that authenticated driver can connect to DriverConsumer."""
    communicator = WebsocketCommunicator(
        application,
        f"/ws/drivers/?token={driver_token}"
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_driver_consumer_anonymous_rejected():
    """Test that anonymous user is rejected from DriverConsumer."""
    communicator = WebsocketCommunicator(
        application,
        "/ws/drivers/"
    )

    connected, code = await communicator.connect()
    # Should be rejected with 4401 Unauthorized
    assert not connected or code == 4401


@pytest.mark.django_db(transaction=True)
def test_websocket_service_send_order_update():
    """Test that WebSocketService can send order updates without crashing."""
    from apps.order.services.websocket_services import WebSocketService
    
    WebSocketService.send_order_update(
        order_id=1,
        data={"status": "confirmed"}
    )


@pytest.mark.django_db(transaction=True)
def test_websocket_service_send_order_management_update():
    """Test that WebSocketService can send order management updates."""
    from apps.order.services.websocket_services import WebSocketService
    
    WebSocketService.send_order_management_update(
        order_id=1,
        data={"status": "confirmed"}
    )

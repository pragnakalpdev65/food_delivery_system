from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.core.constants.choices import UserType
from apps.order.models.order import Order
from apps.restaurant.models.restaurant import Restaurant


UUID_PATH = (
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@database_sync_to_async
def _user_owns_restaurant(user, restaurant_id):
    return Restaurant.objects.filter(id=restaurant_id, owner_id=user.id).exists()


@database_sync_to_async
def _user_can_access_order(user, order_id):
    """Customer, assigned driver, or restaurant owner may join an order room."""
    try:
        order = Order.objects.select_related("restaurant").get(id=order_id)
    except Order.DoesNotExist:
        return False

    if order.customer_id == user.id:
        return True
    if order.driver_id and order.driver_id == user.id:
        return True
    if order.restaurant.owner_id == user.id:
        return True
    return False


class OrderConsumer(AsyncJsonWebsocketConsumer):
    """Real-time updates for a single order: ws/orders/{order_id}/"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]

        if not await _user_can_access_order(user, self.order_id):
            await self.close(code=4403)
            return

        self.group_name = f"order_{self.order_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_order_update(self, event):
        await self.send_json(event["data"])


class OrderManagementConsumer(AsyncJsonWebsocketConsumer):
    """
    Restaurant Order Section WebSocket.

    Endpoint: ws/orders/management/{restaurant_id}/?token=<jwt>

    Events:
    - order_created
    - status_updated
    - driver_assigned
    - new_order
    """

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if getattr(user, "user_type", None) != UserType.RESTAURANT_OWNER:
            await self.close(code=4403)
            return

        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]

        if not await _user_owns_restaurant(user, self.restaurant_id):
            await self.close(code=4403)
            return

        self.group_name = f"restaurant_order_{self.restaurant_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "restaurant_id": str(self.restaurant_id),
                "message": "Connected to restaurant order section",
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_order_update(self, event):
        await self.send_json(event["data"])

    async def send_new_order(self, event):
        await self.send_json(event["data"])


class RestaurantDashboardConsumer(AsyncJsonWebsocketConsumer):
    """Restaurant dashboard WebSocket: ws/restaurants/{restaurant_id}/"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if getattr(user, "user_type", None) != UserType.RESTAURANT_OWNER:
            await self.close(code=4403)
            return

        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]

        if not await _user_owns_restaurant(user, self.restaurant_id):
            await self.close(code=4403)
            return

        self.group_name = f"restaurant_{self.restaurant_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_new_order(self, event):
        await self.send_json(event["data"])

    async def send_order_update(self, event):
        await self.send_json(event["data"])


class CustomerConsumer(AsyncJsonWebsocketConsumer):
    """Customer updates: ws/customers/?token=<jwt>"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if getattr(user, "user_type", None) != UserType.CUSTOMER:
            await self.close(code=4403)
            return

        self.group_name = f"customer_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_order_update(self, event):
        await self.send_json(event["data"])


class DriverConsumer(AsyncJsonWebsocketConsumer):
    """Driver updates: ws/drivers/?token=<jwt>"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if getattr(user, "user_type", None) != UserType.DELIVERY_DRIVER:
            await self.close(code=4403)
            return

        self.group_name = f"driver_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_order_update(self, event):
        await self.send_json(event["data"])

import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.core.constants.choices import UserType
from apps.order.models.order import Order
from apps.restaurant.models.restaurant import Restaurant

logger = logging.getLogger(__name__)

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


class BaseRealtimeConsumer(AsyncJsonWebsocketConsumer):
    """Shared connect helpers: clear rejects + Redis soft-fail."""

    async def _reject(self, code: int, message: str):
        """
        Accept briefly, send an error payload, then close.

        Closing before accept() makes browsers report
        "WebSocket is closed before the connection is established"
        with no useful payload for the frontend.
        """
        await self.accept()
        await self.send_json(
            {
                "event": "error",
                "code": code,
                "message": message,
            }
        )
        await self.close(code=code)

    async def _join_group(self, group_name: str) -> bool:
        """Join a channel group; do not fail the socket if Redis is down."""
        self.group_name = group_name
        if self.channel_layer is None:
            logger.warning("No channel layer configured; realtime fan-out disabled")
            return False
        try:
            await self.channel_layer.group_add(group_name, self.channel_name)
            return True
        except Exception:
            logger.exception(
                "Failed to join channel group %s (is Redis running?)", group_name
            )
            return False

    async def _leave_group(self):
        if not hasattr(self, "group_name") or self.channel_layer is None:
            return
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            logger.exception("Failed to leave channel group %s", self.group_name)


class OrderConsumer(BaseRealtimeConsumer):
    """Real-time updates for a single order: ws/orders/{order_id}/"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self._reject(4401, "Authentication required")
            return

        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]

        if not await _user_can_access_order(user, self.order_id):
            await self._reject(4403, "Not allowed to access this order")
            return

        joined = await self._join_group(f"order_{self.order_id}")
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "order_id": str(self.order_id),
                "realtime_ready": joined,
            }
        )

    async def disconnect(self, close_code):
        await self._leave_group()

    async def send_order_update(self, event):
        await self.send_json(event["data"])


class OrderManagementConsumer(BaseRealtimeConsumer):
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
            await self._reject(4401, "Authentication required. Pass a valid access token.")
            return

        if getattr(user, "user_type", None) != UserType.RESTAURANT_OWNER:
            await self._reject(4403, "Only restaurant owners can open this socket")
            return

        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]

        if not await _user_owns_restaurant(user, self.restaurant_id):
            logger.warning(
                "WebSocket ownership denied user=%s restaurant=%s",
                getattr(user, "id", None),
                self.restaurant_id,
            )
            await self._reject(
                4403,
                "You do not own this restaurant. Use the restaurant id for your account.",
            )
            return

        joined = await self._join_group(f"restaurant_order_{self.restaurant_id}")
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "restaurant_id": str(self.restaurant_id),
                "message": "Connected to restaurant order section",
                "realtime_ready": joined,
            }
        )

    async def disconnect(self, close_code):
        await self._leave_group()

    async def send_order_update(self, event):
        await self.send_json(event["data"])

    async def send_new_order(self, event):
        await self.send_json(event["data"])


class RestaurantDashboardConsumer(BaseRealtimeConsumer):
    """Restaurant dashboard WebSocket: ws/restaurants/{restaurant_id}/"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self._reject(4401, "Authentication required")
            return

        if getattr(user, "user_type", None) != UserType.RESTAURANT_OWNER:
            await self._reject(4403, "Only restaurant owners can open this socket")
            return

        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]

        if not await _user_owns_restaurant(user, self.restaurant_id):
            await self._reject(4403, "You do not own this restaurant")
            return

        joined = await self._join_group(f"restaurant_{self.restaurant_id}")
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "restaurant_id": str(self.restaurant_id),
                "realtime_ready": joined,
            }
        )

    async def disconnect(self, close_code):
        await self._leave_group()

    async def send_new_order(self, event):
        await self.send_json(event["data"])

    async def send_order_update(self, event):
        await self.send_json(event["data"])


class CustomerConsumer(BaseRealtimeConsumer):
    """Customer updates: ws/customers/?token=<jwt>"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self._reject(4401, "Authentication required")
            return

        if getattr(user, "user_type", None) != UserType.CUSTOMER:
            await self._reject(4403, "Only customers can open this socket")
            return

        joined = await self._join_group(f"customer_{user.id}")
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "realtime_ready": joined,
            }
        )

    async def disconnect(self, close_code):
        await self._leave_group()

    async def send_order_update(self, event):
        await self.send_json(event["data"])


class DriverConsumer(BaseRealtimeConsumer):
    """Driver updates: ws/drivers/?token=<jwt>"""

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self._reject(4401, "Authentication required")
            return

        if getattr(user, "user_type", None) != UserType.DELIVERY_DRIVER:
            await self._reject(4403, "Only drivers can open this socket")
            return

        joined = await self._join_group(f"driver_{user.id}")
        await self.accept()
        await self.send_json(
            {
                "event": "connected",
                "realtime_ready": joined,
            }
        )

    async def disconnect(self, close_code):
        await self._leave_group()

    async def send_order_update(self, event):
        await self.send_json(event["data"])

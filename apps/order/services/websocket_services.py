from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)


class WebSocketService:
    """
    Service layer for sending WebSocket messages to connected consumers.

    Groups:
    - order_{order_id}: OrderConsumer
    - restaurant_order_{restaurant_id}: OrderManagementConsumer (restaurant order section)
    - restaurant_{restaurant_id}: RestaurantDashboardConsumer
    - customer_{user_id}: CustomerConsumer
    - driver_{user_id}: DriverConsumer
    """

    @staticmethod
    def _group_send(group, message_type, data):
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        try:
            async_to_sync(channel_layer.group_send)(
                group,
                {
                    "type": message_type,
                    "data": data,
                },
            )
        except Exception:
            # Never fail the HTTP request because realtime delivery is unavailable.
            logger.exception("Failed to publish WebSocket event to group %s", group)

    @staticmethod
    def send_order_update(order_id, data):
        """Send update to clients tracking a specific order."""
        WebSocketService._group_send(
            f"order_{order_id}",
            "send_order_update",
            data,
        )

    @staticmethod
    def send_order_management_update(restaurant_id, data):
        """
        Send update to the restaurant order section.

        Routes to: restaurant_order_{restaurant_id}
        Handled by: OrderManagementConsumer
        """
        WebSocketService._group_send(
            f"restaurant_order_{restaurant_id}",
            "send_order_update",
            data,
        )

    @staticmethod
    def send_restaurant_update(restaurant_id, data):
        """Send new-order notification to restaurant dashboard."""
        WebSocketService._group_send(
            f"restaurant_{restaurant_id}",
            "send_new_order",
            data,
        )

    @staticmethod
    def send_customer_update(user_id, data):
        """Send customer-specific update."""
        WebSocketService._group_send(
            f"customer_{user_id}",
            "send_order_update",
            data,
        )

    @staticmethod
    def send_driver_update(user_id, data):
        """Send driver-specific update."""
        WebSocketService._group_send(
            f"driver_{user_id}",
            "send_order_update",
            data,
        )

    @staticmethod
    def notify_order_created(order):
        """Broadcast order_created to restaurant order section, dashboard, and order room."""
        payload = {
            "event": "order_created",
            "order_id": str(order.id),
            "restaurant_id": str(order.restaurant_id),
            "status": order.status,
            "order_number": order.order_number,
            "total_amount": str(order.total_amount),
        }

        WebSocketService.send_order_management_update(order.restaurant_id, payload)
        WebSocketService.send_restaurant_update(
            order.restaurant_id,
            {
                **payload,
                "event": "new_order",
                "message": "New order received",
            },
        )
        WebSocketService.send_order_update(order.id, payload)
        WebSocketService.send_customer_update(
            order.customer_id,
            {
                "event": "order_created",
                "order_id": str(order.id),
                "status": order.status,
                "message": "Your order has been placed successfully",
            },
        )

    @staticmethod
    def notify_status_updated(order, previous_status=None):
        """Broadcast status_updated to order room and restaurant order section."""
        payload = {
            "event": "status_updated",
            "order_id": str(order.id),
            "restaurant_id": str(order.restaurant_id),
            "status": order.status,
            "previous_status": previous_status,
            "order_number": order.order_number,
        }

        WebSocketService.send_order_update(order.id, payload)
        WebSocketService.send_order_management_update(order.restaurant_id, payload)
        WebSocketService.send_customer_update(order.customer_id, payload)

        if order.driver_id:
            WebSocketService.send_driver_update(order.driver_id, payload)

    @staticmethod
    def notify_driver_assigned(order):
        """Broadcast driver_assigned after a driver is assigned."""
        payload = {
            "event": "driver_assigned",
            "order_id": str(order.id),
            "restaurant_id": str(order.restaurant_id),
            "driver_id": str(order.driver_id) if order.driver_id else None,
            "status": order.status,
            "order_number": order.order_number,
        }

        WebSocketService.send_order_update(order.id, payload)
        WebSocketService.send_order_management_update(order.restaurant_id, payload)
        WebSocketService.send_customer_update(order.customer_id, payload)

        if order.driver_id:
            WebSocketService.send_driver_update(order.driver_id, payload)

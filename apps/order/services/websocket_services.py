from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

class WebSocketService:

    @staticmethod
    def send_order_update(order_id, data):
        async_to_sync(channel_layer.group_send)(
            f"order_{order_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )

    @staticmethod
    def send_restaurant_update(restaurant_id, data):
        async_to_sync(channel_layer.group_send)(
            f"restaurant_{restaurant_id}",
            {
                "type": "send_new_order",
                "data": data
            }
        )

    @staticmethod
    def send_customer_update(user_id, data):
        async_to_sync(channel_layer.group_send)(
            f"customer_{user_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )

    @staticmethod
    def send_driver_update(user_id, data):
        async_to_sync(channel_layer.group_send)(
            f"driver_{user_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )
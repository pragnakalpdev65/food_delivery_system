from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

class WebSocketService:
    """
    Service layer for sending WebSocket messages to connected consumers.
    
    Groups are named to match consumer configurations:
    - order_{order_id}: Generic order updates (OrderConsumer)
    - restaurant_order_{order_id}: Restaurant owner updates (OrderManagementConsumer)
    - restaurant_{restaurant_id}: Restaurant dashboard updates (RestaurantDashboardConsumer)
    - customer_{user_id}: Customer-specific updates (CustomerConsumer)
    - driver_{user_id}: Driver-specific updates (DriverConsumer)
    """

    @staticmethod
    def send_order_update(order_id, data):
        """
        Send order update to customers tracking this specific order.
        
        Routes to: order_{order_id} group
        Handled by: OrderConsumer.send_order_update()
        """
        async_to_sync(channel_layer.group_send)(
            f"order_{order_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )

    @staticmethod
    def send_order_management_update(order_id, data):
        """
        Send order update to restaurant owner managing this order.
        
        Routes to: restaurant_order_{order_id} group
        Handled by: OrderManagementConsumer.send_order_update()
        """
        async_to_sync(channel_layer.group_send)(
            f"restaurant_order_{order_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )

    @staticmethod
    def send_restaurant_update(restaurant_id, data):
        """
        Send new order notification to restaurant dashboard.
        
        Routes to: restaurant_{restaurant_id} group
        Handled by: RestaurantDashboardConsumer.send_new_order()
        """
        async_to_sync(channel_layer.group_send)(
            f"restaurant_{restaurant_id}",
            {
                "type": "send_new_order",
                "data": data
            }
        )

    @staticmethod
    def send_customer_update(user_id, data):
        """
        Send customer-specific update (promotions, recommendations, etc).
        
        Routes to: customer_{user_id} group
        Handled by: CustomerConsumer.send_order_update()
        """
        async_to_sync(channel_layer.group_send)(
            f"customer_{user_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )

    @staticmethod
    def send_driver_update(user_id, data):
        """
        Send driver-specific update (delivery assignments, instructions, etc).
        
        Routes to: driver_{user_id} group
        Handled by: DriverConsumer.send_order_update()
        """
        async_to_sync(channel_layer.group_send)(
            f"driver_{user_id}",
            {
                "type": "send_order_update",
                "data": data
            }
        )
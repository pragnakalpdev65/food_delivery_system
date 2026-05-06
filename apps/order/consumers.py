from channels.generic.websocket import AsyncJsonWebsocketConsumer

class OrderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_group_name = f"order_{self.order_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_order_update(self, event):
        await self.send_json(event["data"])
        
        
        
class OrderManagementConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_group_name = f"order_{self.order_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def send_order_update(self, event):
        await self.send_json(event["data"])
        
        
        
class RestaurantDashboardConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]
        self.room_group_name = f"restaurant_{self.restaurant_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def send_new_order(self, event):
        await self.send_json(event["data"])
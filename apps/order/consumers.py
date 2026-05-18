from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from apps.core.constants.choices import UserType


class OrderConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.order_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_order_update(self, event):
        await self.send_json(event["data"])
        

class OrderManagementConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]
        self.group_name = f"restaurant_order_{self.restaurant_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def send_order_update(self, event):
        await self.send_json(event["data"])

class RestaurantDashboardConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.restaurant_id = self.scope["url_route"]["kwargs"]["restaurant_id"]
        self.group_name = f"restaurant_{self.restaurant_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def send_new_order(self, event):
        await self.send_json(event["data"])
class CustomerConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        await self.accept()
class DriverConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        await self.accept()
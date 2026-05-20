from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from apps.order.models.order import Order, OrderItem
from apps.order.api.v1.serializers.orders import OrderSerializer
from apps.core.constants.messages import AuthMessages
from apps.restaurant.services.availability_service import RestaurantAvailabilityService
from apps.core.constants.error_codes import ErrorCodes
from apps.order.services.websocket_services import WebSocketService

class ReorderSerializer(serializers.Serializer):

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        original_order = self.context["order"]

        restaurant = original_order.restaurant

        if not RestaurantAvailabilityService.is_currently_open(restaurant.id):
            raise serializers.ValidationError(
                {"error": AuthMessages.RESTAURANT_CLOSED}
            )

        unavailable_items = []
        price_changes = []
        valid_items = []

        original_items = original_order.items.select_related("menu_item")

        for item in original_items:
            menu_item = item.menu_item

            if not menu_item or not menu_item.is_available:
                if menu_item:
                    unavailable_items.append(menu_item.name)
                continue

            if menu_item.price != item.price:
                price_changes.append(
                    {
                        "item": menu_item.name,
                        "old_price": item.price,
                        "new_price": menu_item.price,
                    }
                )

            valid_items.append(
                {
                    "menu_item": menu_item,
                    "quantity": item.quantity,
                    "price": menu_item.price,
                }
            )

        if not valid_items:
            raise serializers.ValidationError(
                {"error": AuthMessages.NO_ITEMS_AVAILABLE}
            )

        delivery_address = (
            getattr(request.user, "default_address", None)
            or original_order.delivery_address
        )

        avg_delivery_time = getattr(restaurant, "average_delivery_time", 30)
        estimated_delivery_time = (
            timezone.now() + timedelta(minutes=avg_delivery_time)
        )

        subtotal = Decimal("0.00")
        for item in valid_items:
            subtotal += item["price"] * item["quantity"]

        minimum_order = getattr(restaurant, "minimum_order", None)
        if minimum_order and subtotal < minimum_order:
            raise serializers.ValidationError({
                "error": AuthMessages.MINIMUM_ORDER_NOT_MET,
                "minimum_order": minimum_order,
                "current_subtotal": subtotal,
            })

        delivery_fee = restaurant.delivery_fee or Decimal("0.00")
        tax_rate = Decimal(str(restaurant.tax_rate or 0.05))

        tax = (subtotal * tax_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        total = (subtotal + tax + delivery_fee).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        new_order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            delivery_address=delivery_address,
            estimated_delivery_time=estimated_delivery_time,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            tax=tax,
            total=total,
        )

        order_items = [
            OrderItem(
                order=new_order,
                menu_item=item["menu_item"],
                quantity=item["quantity"],
                price=item["price"],
            )
            for item in valid_items
        ]

        OrderItem.objects.bulk_create(order_items)

        WebSocketService.send_customer_update(
            user_id=new_order.customer.id,
            data={
                "event": "order_created",
                "order_id": str(new_order.id),
                "message": "Your reorder has been placed successfully",
            }
        )

        WebSocketService.send_restaurant_update(
            restaurant_id=new_order.restaurant.id,
            data={
                "event": "new_order",
                "order_id": str(new_order.id),
                "message": "New reorder received",
            }
        )

        WebSocketService.send_order_update(
            order_id=new_order.id,
            data={
                "event": "order_created",
                "status": new_order.status,
            }
        )

        return {
            "order": OrderSerializer(
                new_order,
                context={"request": request}
            ).data,
            "unavailable_items": unavailable_items,
            "price_changes": price_changes,
        }
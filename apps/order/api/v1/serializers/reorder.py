from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from apps.order.models.order import Order, OrderItem
from apps.order.api.v1.serializers.orders import OrderSerializer
from apps.core.constants.messages import AuthMessages
from apps.restaurant.services.availability_service import RestaurantAvailabilityService


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

        delivery_fee = restaurant.delivery_fee
        tax_rate = Decimal(str(restaurant.tax_rate or 0.05))
        tax = subtotal * tax_rate
        new_order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            delivery_address=delivery_address,
            estimated_delivery_time=estimated_delivery_time,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            tax=tax,
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

        new_order.calculate_total()
        new_order.save(update_fields=["total"])


        return {
            "order": OrderSerializer(
                new_order,
                context={"request": request}
            ).data,
            "unavailable_items": unavailable_items,
            "price_changes": price_changes,
        }
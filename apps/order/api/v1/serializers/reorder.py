from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework import serializers

from apps.order.models.order import (
    Order,
    OrderItem
)

from apps.order.api.v1.serializers.orders import (
    OrderSerializer
)

from apps.core.constants.messages import AuthMessages


class ReorderSerializer(serializers.Serializer):

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        original_order = self.context["order"]

        restaurant = original_order.restaurant

        if not restaurant.is_open:
            raise serializers.ValidationError(
                {
                    "error": AuthMessages.RESTAURANT_CLOSED
                }
            )

        unavailable_items = []
        price_changes = []
        valid_items = []

        original_items = (
            original_order.items.select_related(
                "menu_item"
            )
        )

        for item in original_items:
            menu_item = item.menu_item

            if (
                not menu_item
                or not menu_item.is_available
            ):
                unavailable_items.append(
                    menu_item.name
                )
                continue

            if menu_item.price != item.price:
                price_changes.append(
                    {
                        "item": menu_item.name,
                        "old_price": item.price,
                        "new_price": menu_item.price
                    }
                )

            valid_items.append(
                {
                    "menu_item": menu_item,
                    "quantity": item.quantity
                }
            )

        if not valid_items:
            raise serializers.ValidationError(
                {
                    "error": AuthMessages.NO_ITEMS_AVAILABLE
                }
            )

        new_order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            delivery_address=(
                original_order.delivery_address
            ),
            estimated_delivery_time=(
                timezone.now()
                + timedelta(minutes=30)
            )
        )

        subtotal = Decimal("0.00")

        order_items = []

        for item in valid_items:
            menu_item = item["menu_item"]
            quantity = item["quantity"]

            subtotal += (
                menu_item.price * quantity
            )

            order_items.append(
                OrderItem(
                    order=new_order,
                    menu_item=menu_item,
                    quantity=quantity,
                    price=menu_item.price
                )
            )

        OrderItem.objects.bulk_create(
            order_items
        )

        new_order.subtotal = subtotal
        new_order.delivery_fee = (
            restaurant.delivery_fee
        )
        new_order.tax = (
            subtotal * Decimal("0.05")
        )

        new_order.calculate_total()
        new_order.save()

        return {
            "order": OrderSerializer(
                new_order,
                context={
                    "request": request
                }
            ).data,
            "unavailable_items": (
                unavailable_items
            ),
            "price_changes": (
                price_changes
            )
        }
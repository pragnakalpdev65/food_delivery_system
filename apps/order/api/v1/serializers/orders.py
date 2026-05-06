from rest_framework import serializers
from django.db import transaction

from apps.order.models.order import Order
from apps.order.models.order import OrderItem
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['id','restaurant','delivery_address','items','subtotal','delivery_fee','tax','total_amount','status','created_at']
        read_only_fields = ['subtotal','delivery_fee','tax','total_amount','status','created_at']

    def validate(self, data):
        items = data.get('items')
        restaurant = data.get('restaurant')

        if not items:
            raise serializers.ValidationError("Order must contain at least one item")

        for item in items:
            menu_item = item['menu_item']
            if menu_item.restaurant != restaurant:
                raise serializers.ValidationError(
                    "All items must belong to the selected restaurant"
                )
            if not menu_item.is_available:
                raise serializers.ValidationError(
                    f"'{menu_item.name}' is currently unavailable"
                )
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        order = Order.objects.create(
            customer=user,
            estimated_delivery_time=timezone.now() + timedelta(minutes=30),
            **validated_data
        )

        subtotal = Decimal("0.00")
        order_items = []

        for item in items_data:
            menu_item = item['menu_item']
            quantity = item['quantity']

            price = menu_item.price
            subtotal += price * quantity

            order_items.append(
                OrderItem(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    price=price
                )
            )

        OrderItem.objects.bulk_create(order_items)

        order.subtotal = subtotal
        order.delivery_fee = order.restaurant.delivery_fee
        order.tax = subtotal * Decimal("0.05")
        order.calculate_total()

        if order.subtotal < order.restaurant.minimum_order:
            raise serializers.ValidationError(
                f"Order total must meet the restaurant's minimum order of {order.restaurant.minimum_order}"
            )

        order.save()
        return order
    
    def update(self, instance, validated_data):
        instance.delivery_fee = validated_data.get('delivery_fee', instance.delivery_fee)
        instance.tax = validated_data.get('tax', instance.tax)

        instance.calculate_total()
        instance.save()

        return instance
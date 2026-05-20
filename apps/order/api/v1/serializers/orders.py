from rest_framework import serializers
from django.db import transaction

from apps.order.models.order import Order
from apps.order.models.order import OrderItem
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from apps.core.constants.messages import AuthMessages
from apps.restaurant.services.availability_service import RestaurantAvailabilityService
from apps.core.constants.messages import AuthMessages

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity','special_instructions']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(AuthMessages.REQUIRED_QUANTITY)
        return value
    
    def validate_special_instructions(self, value):
        if value and len(value) > 200:
            raise serializers.ValidationError(AuthMessages.MAX_200_CHAR_ALLOWED)
        return value

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    delivery_instructions = serializers.CharField(required=False,allow_blank=True,max_length=500)
    class Meta:
        model = Order
        fields = ['id','restaurant','delivery_address','items','subtotal','delivery_fee','tax','total_amount','status','created_at', 'delivery_instructions','contact_preference','utensils_required','contactless_delivery',]
        read_only_fields = ['id','subtotal','delivery_fee','tax','total_amount','status','created_at']

    def validate_delivery_instructions(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError(AuthMessages.MAX_500_CHAR_ALLOWED)
        return value
    def validate(self, data):
        items = data.get('items')
        restaurant = data.get('restaurant')

        if not items:
            raise serializers.ValidationError(AuthMessages.CONTAIN_ONE_ITEM)

        for item in items:
            menu_item = item['menu_item']
            if menu_item.restaurant != restaurant:
                raise serializers.ValidationError(AuthMessages.ITEM_BELONGS_TO_ONE_RESTAURANT
                    
                )
            if not menu_item.is_available:
                raise serializers.ValidationError(
                        AuthMessages.MENU_ITEM_UNAVAILABLE % {
                        "item_name": menu_item.name
                    }
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
                    price=price,
                    special_instructions=item.get("special_instructions")
                )
            )

        OrderItem.objects.bulk_create(order_items)

        order.subtotal = subtotal
        order.delivery_fee = order.restaurant.delivery_fee
        order.tax = subtotal * Decimal("0.05")
        order.calculate_total()

        if order.subtotal < order.restaurant.minimum_order:
            raise serializers.ValidationError(
                AuthMessages.MINIMUM_ORDER_NOT_MET % {
                    "minimum_order": order.restaurant.minimum_order
                }        
                )

        order.save()
        return order
    
    def update(self, instance, validated_data):
        instance.delivery_fee = validated_data.get('delivery_fee', instance.delivery_fee)
        instance.tax = validated_data.get('tax', instance.tax)

        instance.calculate_total()
        instance.save()

        return instance   
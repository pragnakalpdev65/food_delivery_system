from rest_framework import serializers
from django.db.models import Sum, Avg, Count

from apps.order.models.order import Order, OrderItem
from apps.core.constants.choices import OrderStatus


class FavoriteRestaurantSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    order_count = serializers.IntegerField()


class MostOrderedItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    order_count = serializers.IntegerField()


class OrderStatusSerializer(serializers.Serializer):
    delivered = serializers.IntegerField()
    cancelled = serializers.IntegerField()


class OrderStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    favorite_restaurant = FavoriteRestaurantSerializer(allow_null=True)
    most_ordered_item = MostOrderedItemSerializer(allow_null=True)
    orders_by_status = OrderStatusSerializer()

    def to_representation(self, instance):
        request = self.context["request"]

        base_orders = Order.objects.filter(customer=request.user)
        active_orders = base_orders.exclude(status=OrderStatus.CANCELLED)
        total_orders = active_orders.count()

        total_spent = (
            active_orders.aggregate(total=Sum("total_amount"))["total"] or 0
        )

        average_order_value = (
            active_orders.aggregate(avg=Avg("total_amount"))["avg"] or 0
        )

        favorite_restaurant = (
            active_orders.values("restaurant__id", "restaurant__name")
            .annotate(order_count=Count("id"))
            .order_by("-order_count")
            .first()
        )

        most_ordered_item = (
            OrderItem.objects.filter(order__customer=request.user)
            .values("menu_item__id", "menu_item__name")
            .annotate(order_count=Sum("quantity"))
            .order_by("-order_count")
            .first()
        )

        delivered_count = base_orders.filter(
            status=OrderStatus.DELIVERED
        ).count()

        cancelled_count = base_orders.filter(
            status=OrderStatus.CANCELLED
        ).count()

        return {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "average_order_value": average_order_value,
            "favorite_restaurant": (
                {
                    "id": favorite_restaurant["restaurant__id"],
                    "name": favorite_restaurant["restaurant__name"],
                    "order_count": favorite_restaurant["order_count"],
                }
                if favorite_restaurant
                else None
            ),
            "most_ordered_item": (
                {
                    "id": most_ordered_item["menu_item__id"],
                    "name": most_ordered_item["menu_item__name"],
                    "order_count": most_ordered_item["order_count"],
                }
                if most_ordered_item
                else None
            ),
            "orders_by_status": {
                "delivered": delivered_count,
                "cancelled": cancelled_count,
            },
        }
        
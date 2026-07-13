from datetime import timedelta

from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from rest_framework import serializers

from apps.order.models.order import Order, OrderItem
from apps.core.constants.choices import OrderStatus


class OrderStatsFavoriteRestaurantSerializer(serializers.Serializer):
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


class WeeklyRevenueSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class ItemPopularitySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    total_quantity = serializers.IntegerField()


class PopularTimingSerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    order_count = serializers.IntegerField()


class OrderStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    favorite_restaurant = OrderStatsFavoriteRestaurantSerializer(
        allow_null=True
    )
    most_ordered_item = MostOrderedItemSerializer(
        allow_null=True
    )
    orders_by_status = OrderStatusSerializer()

    # New Analytics Fields
    weekly_revenue_trend = WeeklyRevenueSerializer(many=True)
    item_popularity = ItemPopularitySerializer(many=True)
    popular_timing = PopularTimingSerializer(many=True)

    def to_representation(self, instance):
        request = self.context["request"]

        base_orders = Order.objects.filter(
            customer=request.user
        )

        active_orders = base_orders.exclude(
            status=OrderStatus.CANCELLED
        )

        total_orders = active_orders.count()

        total_spent = (
            active_orders.aggregate(
                total=Sum("total_amount")
            )["total"] or 0
        )

        average_order_value = (
            active_orders.aggregate(
                avg=Avg("total_amount")
            )["avg"] or 0
        )

        favorite_restaurant = (
            active_orders.values(
                "restaurant__id",
                "restaurant__name"
            )
            .annotate(
                order_count=Count("id")
            )
            .order_by("-order_count")
            .first()
        )

        most_ordered_item = (
            OrderItem.objects.filter(
                order__customer=request.user
            )
            .values(
                "menu_item__id",
                "menu_item__name"
            )
            .annotate(
                order_count=Sum("quantity")
            )
            .order_by("-order_count")
            .first()
        )

        delivered_count = base_orders.filter(
            status=OrderStatus.DELIVERED
        ).count()

        cancelled_count = base_orders.filter(
            status=OrderStatus.CANCELLED
        ).count()

        # ----------------------------
        # Restaurant Specific Analytics
        # ----------------------------
        weekly_revenue_trend = []
        item_popularity = []
        popular_timing = []

        if favorite_restaurant:
            restaurant_id = favorite_restaurant["restaurant__id"]

            last_week = timezone.now() - timedelta(days=7)

            # Recent Week Revenue Trend
            weekly_revenue_trend = (
                Order.objects.filter(
                    customer=request.user,
                    restaurant_id=restaurant_id,
                    created_at__gte=last_week,
                )
                .exclude(
                    status=OrderStatus.CANCELLED
                )
                .annotate(
                    date=TruncDate("created_at")
                )
                .values("date")
                .annotate(
                    revenue=Sum("total_amount")
                )
                .order_by("date")
            )

            # Item Popularity
            item_popularity = (
                OrderItem.objects.filter(
                    order__customer=request.user,
                    order__restaurant_id=restaurant_id,
                )
                .values(
                    "menu_item__id",
                    "menu_item__name"
                )
                .annotate(
                    total_quantity=Sum("quantity")
                )
                .order_by("-total_quantity")
            )

            # Popular Restaurant Timing
            popular_timing = (
                Order.objects.filter(
                    customer=request.user,
                    restaurant_id=restaurant_id,
                )
                .exclude(
                    status=OrderStatus.CANCELLED
                )
                .annotate(
                    hour=ExtractHour("created_at")
                )
                .values("hour")
                .annotate(
                    order_count=Count("id")
                )
                .order_by("hour")
            )

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
            "weekly_revenue_trend": [
                {
                    "date": item["date"],
                    "revenue": item["revenue"] or 0,
                }
                for item in weekly_revenue_trend
            ],
            "item_popularity": [
                {
                    "id": item["menu_item__id"],
                    "name": item["menu_item__name"],
                    "total_quantity": item["total_quantity"] or 0,
                }
                for item in item_popularity
            ],
            "popular_timing": [
                {
                    "hour": item["hour"],
                    "order_count": item["order_count"],
                }
                for item in popular_timing
            ],
        }
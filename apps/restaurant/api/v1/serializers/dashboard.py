from datetime import timedelta

from decimal import Decimal

from django.db.models import Avg, Count, Min, Q, Sum
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from rest_framework import serializers

from apps.core.constants.choices import OrderStatus
from apps.order.models.order import Order, OrderItem
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant

ACTIVE_ORDER_STATUSES = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.PICKED_UP,
]


class DashboardRevenueTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class DashboardCategorySalesSerializer(serializers.Serializer):
    category = serializers.CharField()
    total_orders = serializers.IntegerField()
    percentage = serializers.FloatField()


class DashboardPopularTimeSerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    order_count = serializers.IntegerField()


class AnalyticsPackSerializer(serializers.Serializer):
    revenue_trends = DashboardRevenueTrendSerializer(many=True)
    sales_by_category = DashboardCategorySalesSerializer(many=True)
    popular_times = DashboardPopularTimeSerializer(many=True)


class RestaurantDashboardSerializer(serializers.Serializer):
    restaurant_id = serializers.UUIDField()
    restaurant_name = serializers.CharField()
    active_orders = serializers.IntegerField()
    daily_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    new_customers = serializers.IntegerField()
    total_menu_items = serializers.IntegerField()
    net_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    analytics = AnalyticsPackSerializer()

    def to_representation(self, restaurant: Restaurant):
        today = timezone.localdate()
        last_week = timezone.now() - timedelta(days=7)

        orders = Order.objects.filter(restaurant=restaurant)
        delivered_orders = orders.filter(status=OrderStatus.DELIVERED)

        active_orders = orders.filter(status__in=ACTIVE_ORDER_STATUSES).count()

        daily_revenue = (
            delivered_orders.filter(
                Q(actual_delivery_time__date=today)
                | Q(actual_delivery_time__isnull=True, created_at__date=today)
            ).aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0.00")
        )

        # Customers whose first order at this restaurant was placed today.
        new_customers = (
            orders.values("customer_id")
            .annotate(first_order_at=Min("created_at"))
            .filter(first_order_at__date=today)
            .count()
        )

        total_menu_items = MenuItem.objects.filter(restaurant=restaurant).count()

        net_revenue = (
            delivered_orders.aggregate(total=Sum("total_amount"))["total"] or 0
        )
        total_orders = orders.exclude(status=OrderStatus.CANCELLED).count()
        average_order_value = (
            delivered_orders.aggregate(avg=Avg("total_amount"))["avg"] or 0
        )

        revenue_trends = (
            delivered_orders.filter(created_at__gte=last_week)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(revenue=Sum("total_amount"))
            .order_by("date")
        )

        category_rows = (
            OrderItem.objects.filter(
                order__restaurant=restaurant,
                order__status=OrderStatus.DELIVERED,
            )
            .values("menu_item__category")
            .annotate(total_orders=Sum("quantity"))
            .order_by("-total_orders")
        )
        category_total = sum(row["total_orders"] for row in category_rows) or 1

        popular_times = (
            delivered_orders.annotate(hour=ExtractHour("created_at"))
            .values("hour")
            .annotate(order_count=Count("id"))
            .order_by("hour")
        )

        return {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "active_orders": active_orders,
            "daily_revenue": f"{Decimal(daily_revenue):.2f}",
            "new_customers": new_customers,
            "total_menu_items": total_menu_items,
            "net_revenue": f"{Decimal(net_revenue):.2f}",
            "total_orders": total_orders,
            "average_order_value": f"{Decimal(average_order_value):.2f}",
            "average_rating": f"{Decimal(restaurant.average_rating):.2f}",
            "analytics": {
                "revenue_trends": [
                    {
                        "date": row["date"],
                        "revenue": f"{Decimal(row['revenue'] or 0):.2f}",
                    }
                    for row in revenue_trends
                ],
                "sales_by_category": [
                    {
                        "category": row["menu_item__category"],
                        "total_orders": row["total_orders"],
                        "percentage": round(
                            (row["total_orders"] / category_total) * 100,
                            2,
                        ),
                    }
                    for row in category_rows
                ],
                "popular_times": [
                    {
                        "hour": row["hour"],
                        "order_count": row["order_count"],
                    }
                    for row in popular_times
                ],
            },
        }

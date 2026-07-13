from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.services.availability_service import RestaurantAvailabilityService
from django.db.models import Avg, Sum, Count
from apps.order.models.order import Order
from apps.core.constants.choices import OrderStatus
from datetime import timedelta
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone

from apps.order.models.order import Order, OrderItem
from apps.core.constants.choices import OrderStatus
class RestaurantSerializer(serializers.ModelSerializer):

    average_rating = serializers.FloatField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    favorite_count = serializers.IntegerField(read_only=True)
    is_open_now = serializers.SerializerMethodField()
    next_opening_time = serializers.SerializerMethodField()

    # New Fields
    net_revenue = serializers.SerializerMethodField()
    average_order_value = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "address",
            "cuisine_type",
            "email",
            "opening_time",
            "closing_time",
            "delivery_fee",
            "minimum_order",
            "logo",
            "average_rating",
            "is_favorited",
            "favorite_count",
            "is_open_now",
            "next_opening_time",
            "net_revenue",
            "average_order_value",
        ]
        read_only_fields = ["id", "owner"]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_favorited(self, obj):
        request = self.context.get("request")

        if not request or request.user.is_anonymous:
            return False

        return obj.favorited_by.filter(
            customer=request.user
        ).exists()

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_open_now(self, obj):
        return RestaurantAvailabilityService.is_currently_open(obj)

    @extend_schema_field(OpenApiTypes.STR)
    def get_next_opening_time(self, obj):
        return RestaurantAvailabilityService.get_next_opening_time(obj)

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_net_revenue(self, obj):
        return (
            Order.objects.filter(
                restaurant=obj,
                status=OrderStatus.DELIVERED,
            ).aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_average_order_value(self, obj):
        return (
            Order.objects.filter(
                restaurant=obj,
                status=OrderStatus.DELIVERED,
            ).aggregate(
                avg=Avg("total_amount")
            )["avg"]
            or 0
        )
class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields = ["id","name","logo","address","opening_time"]
 
class RevenueTrendSerializer(serializers.Serializer):
    date = serializers.DateField()
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class CategorySalesSerializer(serializers.Serializer):
    category = serializers.CharField()
    total_orders = serializers.IntegerField()
    percentage = serializers.FloatField()


class PopularTimeSerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    order_count = serializers.IntegerField()       
class RestaurantDetailSerializer(serializers.ModelSerializer):
    revenue_trends = serializers.SerializerMethodField()
    sales_by_category = serializers.SerializerMethodField()
    popular_times = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "name",
            "description",
            "cuisine_type",
            "address",
            "phone_number",
            "email",
            "logo",
            "banner",
            "opening_time",
            "closing_time",
            "is_open",
            "delivery_fee",
            "minimum_order",
            "average_rating",
            "total_reviews",
            "revenue_trends",
            "sales_by_category",
            "popular_times",
        ]
        read_only_fields = ["id", "owner"]

    @extend_schema_field(RevenueTrendSerializer(many=True))
    def get_revenue_trends(self, obj):
        last_week = timezone.now() - timedelta(days=7)

        data = (
            Order.objects.filter(
                restaurant=obj,
                status=OrderStatus.DELIVERED,
                created_at__gte=last_week,
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

        return [
            {
                "date": item["date"],
                "revenue": item["revenue"] or 0,
            }
            for item in data
        ]

    @extend_schema_field(CategorySalesSerializer(many=True))
    def get_sales_by_category(self, obj):
        items = (
            OrderItem.objects.filter(
                order__restaurant=obj,
                order__status=OrderStatus.DELIVERED,
            )
            .values("menu_item__category")
            .annotate(
                total_orders=Sum("quantity")
            )
            .order_by("-total_orders")
        )

        total = (
            sum(item["total_orders"] for item in items)
            or 1
        )

        return [
            {
                "category": item["menu_item__category"],
                "total_orders": item["total_orders"],
                "percentage": round(
                    (item["total_orders"] / total) * 100,
                    2,
                ),
            }
            for item in items
        ]

    @extend_schema_field(PopularTimeSerializer(many=True))
    def get_popular_times(self, obj):
        data = (
            Order.objects.filter(
                restaurant=obj,
                status=OrderStatus.DELIVERED,
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

        return [
            {
                "hour": item["hour"],
                "order_count": item["order_count"],
            }
            for item in data
        ]
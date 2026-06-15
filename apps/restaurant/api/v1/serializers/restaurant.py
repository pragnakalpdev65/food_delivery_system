from rest_framework import serializers
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.services.availability_service import RestaurantAvailabilityService
from django.db.models import Avg, Sum
from apps.order.models.order import Order
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

    def get_is_favorited(self, obj):
        request = self.context.get("request")

        if not request or request.user.is_anonymous:
            return False

        return obj.favorited_by.filter(
            customer=request.user
        ).exists()

    def get_is_open_now(self, obj):
        return RestaurantAvailabilityService.is_currently_open(obj)

    def get_next_opening_time(self, obj):
        return RestaurantAvailabilityService.get_next_opening_time(obj)

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
        fields = ["id","name","address","opening_time"]
        
class RestaurantDetailSerializer(serializers.ModelSerializer):
    net_revenue = serializers.SerializerMethodField()
    average_order_value = serializers.SerializerMethodField()

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
            "net_revenue",
            "average_order_value",
        ]
        read_only_fields = ["id", "owner"]

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
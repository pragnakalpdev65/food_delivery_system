from rest_framework import serializers
from apps.restaurant.models.restaurant import Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        # fields = ["id", "name", "address"]
        fields = [
            "id", "name", "address", "cuisine_type", 
            "opening_time", "closing_time", "delivery_fee", "minimum_order"
        ]
        read_only_fields = ["owner", "rating"]


class RestaurantDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"
               
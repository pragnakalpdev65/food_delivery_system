from rest_framework import serializers
from apps.restaurant.models.restaurant import Restaurant

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "id", "name", "address", "cuisine_type", "email",
            "opening_time", "closing_time", "delivery_fee", "minimum_order","logo"
        ]
        read_only_fields = ["id", "owner"]
class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields = ["id","name","address","opening_time"]
        
class RestaurantDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["name", "description", "cuisine_type", "address", "phone_number", "email", "logo", "banner", "opening_time", "closing_time", "is_open", "delivery_fee", "minimum_order" , "average_rating", "total_reviews"]
        read_only_fields = ["id", "owner"]
               
from rest_framework import serializers
from apps.restaurant.models.restaurant import Restaurant

class RestaurantSerializer(serializers.ModelSerializer):
    
    average_rating = serializers.FloatField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    favorite_count = serializers.IntegerField(
        source="favorited_by.count",
        read_only=True,
    )
    class Meta:
        model = Restaurant
        fields = [
            "id", "name", "address", "cuisine_type", "email",
            "opening_time", "closing_time", "delivery_fee", "minimum_order","logo","average_rating","is_favorited",
            "favorite_count",

        ]
        read_only_fields = ["id", "owner"]
        
    def get_is_favorited(self, obj):
        request = self.context.get("request")

        if not request or request.user.is_anonymous:
            return False

        return obj.favorited_by.filter(
            customer=request.user
        ).exists()
class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields = ["id","name","address","opening_time"]
        
class RestaurantDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["name", "description", "cuisine_type", "address", "phone_number", "email", "logo", "banner", "opening_time", "closing_time", "is_open", "delivery_fee", "minimum_order" , "average_rating", "total_reviews"]
        read_only_fields = ["id", "owner"]
               
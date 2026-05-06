from rest_framework import serializers
from apps.restaurant.models.restaurant import Restaurant
from rest_framework.serializers import ValidationError


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "id", "name", "address", "cuisine_type", "email",
            "opening_time", "closing_time", "delivery_fee", "minimum_order","logo"
        ]
        read_only_fields = ["id", "owner"]
        
    # def validate_logo(self,value):
    #     if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
    #             raise ValidationError("Only JPG, JPEG, and PNG formats are allowed.")
            
    #     if value.size > 5 * 1024 * 1024:
    #         raise ValidationError("Logo must be less than 5MB")

    # def validate_banner(self,value):
    #     if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
    #             raise ValidationError("Only JPG, JPEG, and PNG formats are allowed.")
        
    #     if value.size > 10 * 1024 * 1024:
    #         raise ValidationError("Banner must be less than 10MB")
    

class RestaurantListSerializer(serializers.ModelSerializer):
    class Meta:
        model=Restaurant
        fields = ["id","name","address","opening_time"]
        
class RestaurantDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["owner", "name", "description", "cuisine_type", "address", "phone_number", "email", "logo", "banner", "opening_time", "closing_time", "is_open", "delivery_fee", "minimum_order" , "average_rating", "total_reviews"]
        read_only_fields = ["id", "owner"]
               
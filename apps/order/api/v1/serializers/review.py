from rest_framework import serializers
from apps.order.models import Review
from rest_framework.serializers import ValidationError     
class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ["id", "order", "restaurant", "menu_item", "rating", "comment"]

    def validate_rating(self,value):
        if value < 1 or value > 5:
            raise ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate(self, data):
        order = data["order"]
        user = self.context["request"].user

        if order.customer != user:
            raise ValidationError("You can only review your own order")

        if order.status != "delivered":
            raise ValidationError("Order must be delivered to review")

        return data

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)
from rest_framework import serializers
from apps.core.constants.status import OrderStatus
from apps.order.models import Review
from rest_framework.serializers import ValidationError   
from apps.core.constants.messages import AuthMessages  
class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = ["id", "order", "restaurant", "menu_item", "rating", "comment"]

    def validate_rating(self,value):
        if value < 1 or value > 5:
            raise ValidationError(AuthMessages.RATING_VALIDATION)
        return value
    
    def validate(self, data):
        order = data["order"]
        user = self.context["request"].user

        if order.customer != user:
            raise ValidationError(AuthMessages.REVIEW_OWN_ORDER)

        if order.status != OrderStatus.DELIVERED:
            raise ValidationError(AuthMessages.REVIEW_DELIVERED_ORDER)

        return data

    def create(self, validated_data):
        validated_data["customer"] = self.context["request"].user
        return super().create(validated_data)
from rest_framework import serializers
from apps.restaurant.models.menu import MenuItem

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from apps.restaurant.models.menu import MenuItem
from apps.core.constants.messages import AuthMessages

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user

        # 1. Validation Logic
        if user.user_type != "Restaurant Owner":
            raise PermissionDenied(AuthMessages. ADD_MENU_PERMISSION_DENIED)

        restaurant = validated_data.get('restaurant')
        if restaurant.owner != user:
            raise PermissionDenied(AuthMessages. ADD_MENU_PERMISSION_DENIED)

        # 2. Manual creation instead of super()
        # **validated_data unpacks the dictionary into model fields
        instance = MenuItem.objects.create(**validated_data)
        
        return instance


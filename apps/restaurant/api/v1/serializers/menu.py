from rest_framework import serializers
from apps.restaurant.models.menu import MenuItem

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from apps.restaurant.models.menu import MenuItem
from apps.core.constants.messages import AuthMessages

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["restaurant", "name", "description", "price", "category", "dietary_info", "image", "is_available", "preparation_time"]    
        
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        
        if (user.user_type != "restaurant_owner" and user.user_type != "Restaurant Owner"):
            raise PermissionDenied(AuthMessages. ADD_MENU_PERMISSION_DENIED)

        restaurant = validated_data.get('restaurant')
        if restaurant.owner != user:
            raise PermissionDenied(AuthMessages. ADD_MENU_PERMISSION_DENIED)
        
        instance = MenuItem.objects.create(**validated_data)
        
        return instance

class MenuItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "name", "price", "is_available"]

class MenuItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["restaurant", "name", "description", "price", "category", "dietary_info", "image", "is_available", "preparation_time"]
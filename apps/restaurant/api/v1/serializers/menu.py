from rest_framework import serializers
from apps.restaurant.models.menu import MenuItem

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["restaurant", "name", "description", "price", "category", "dietary_info", "image", "is_available", "preparation_time"]    
        
    def create(self, validated_data):
        # Permission checks are now handled by IsMenuItemOwner permission class
        # Ownership validation happens at the permission level, not in the serializer
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
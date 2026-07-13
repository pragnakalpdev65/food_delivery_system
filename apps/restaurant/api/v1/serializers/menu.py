from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from apps.restaurant.models.menu import MenuItem

class MenuItemSerializer(serializers.ModelSerializer):
    
    is_favorited = serializers.SerializerMethodField()
    favorite_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = MenuItem
        fields = ["id", "restaurant", "name", "description", "price", "category", "dietary_info", "image", "is_available", "preparation_time","is_favorited",
            "favorite_count",]    
        
    def create(self, validated_data):
        # Permission checks are now handled by IsMenuItemOwner permission class
        # Ownership validation happens at the permission level, not in the serializer
        instance = MenuItem.objects.create(**validated_data)
        return instance
    
    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_favorited(self, obj):
        request = self.context.get("request")

        if not request or request.user.is_anonymous:
            return False

        return obj.favorited_by.filter(
            customer=request.user
        ).exists()

class MenuItemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "name", "price", "is_available"]

class MenuItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["restaurant", "name", "description", "price", "category", "dietary_info", "image", "is_available", "preparation_time"]
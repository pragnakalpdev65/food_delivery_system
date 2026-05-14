from rest_framework import serializers

from apps.users.models import FavoriteRestaurant, FavoriteMenuItem
from apps.restaurant.api.v1.serializers.restaurant import RestaurantSerializer
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer


class FavoriteRestaurantSerializer(serializers.ModelSerializer):
    restaurant = RestaurantSerializer(read_only=True)

    class Meta:
        model = FavoriteRestaurant
        fields = [
            "id",
            "restaurant",
            "created_at",
        ]


class FavoriteMenuItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)

    class Meta:
        model = FavoriteMenuItem
        fields = [
            "id",
            "menu_item",
            "created_at",
        ]
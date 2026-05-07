from django.core.cache import cache
from apps.core.constants.cache_keys import CacheKey
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.api.v1.serializers.restaurant import (
    RestaurantListSerializer,
    RestaurantDetailSerializer
)
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer

class RestaurantCacheService:

    @staticmethod
    def get_restaurant_list(queryset):
        cache_key = CacheKey.RESTAURANT_LIST

        data = cache.get(cache_key)
        if data:
            return data

        data = RestaurantListSerializer(queryset, many=True).data
        cache.set(cache_key, data, timeout=60 * 5)
        return data

    @staticmethod
    def get_restaurant_detail(restaurant):
        cache_key = CacheKey.RESTAURANT_DETAIL % restaurant.id

        data = cache.get(cache_key)
        if data:
            return data

        data = RestaurantDetailSerializer(restaurant).data
        cache.set(cache_key, data, timeout=60 * 10)
        return data

    @staticmethod
    def get_restaurant_menu(restaurant_id):
        cache_key = CacheKey.RESTAURANT_MENU % restaurant_id

        data = cache.get(cache_key)
        if data:
            return data
        menu_items = MenuItem.objects.filter(restaurant_id=restaurant_id)
        data = MenuItemSerializer(menu_items, many=True).data

        cache.set(cache_key, data, timeout=60 * 15)
        return data

    @staticmethod
    def get_popular_restaurants():
        cache_key = CacheKey.POPULAR_RESTAURANTS

        data = cache.get(cache_key)
        if data:
            return data

        restaurants = Restaurant.objects.order_by("-average_rating")[:10]
        data = RestaurantListSerializer(restaurants, many=True).data

        cache.set(cache_key, data, timeout=60 * 30)
        return data

    @staticmethod
    def clear_restaurant_list():
        cache.delete(CacheKey.RESTAURANT_LIST)

    @staticmethod
    def clear_restaurant_detail(restaurant_id):
        cache.delete(CacheKey.RESTAURANT_DETAIL % restaurant_id)

    @staticmethod
    def clear_restaurant_menu(restaurant_id):
        cache.delete(CacheKey.RESTAURANT_MENU % restaurant_id)

    @staticmethod
    def clear_popular_restaurants():
        cache.delete(CacheKey.POPULAR_RESTAURANTS)
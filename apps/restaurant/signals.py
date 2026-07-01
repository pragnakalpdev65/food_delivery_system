from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.services.cache_services import RestaurantCacheService

@receiver(post_save, sender=MenuItem)
def clear_menu_cache_on_save(sender, instance, **kwargs):
    """Clear restaurant menu cache when a MenuItem is created or updated."""
    RestaurantCacheService.clear_restaurant_menu(instance.restaurant.id)

@receiver(post_delete, sender=MenuItem)
def clear_menu_cache_on_delete(sender, instance, **kwargs):
    """Clear restaurant menu cache when a MenuItem is deleted."""
    RestaurantCacheService.clear_restaurant_menu(instance.restaurant.id)

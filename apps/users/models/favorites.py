from django.db import models

from apps.users.models import CustomUser
from apps.restaurant.models import Restaurant
from apps.restaurant.models import MenuItem


class FavoriteRestaurant(models.Model):
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="favorite_restaurants",
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["customer", "restaurant"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.email} -> {self.restaurant.name}"


class FavoriteMenuItem(models.Model):
    customer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="favorite_items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["customer", "menu_item"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.email} -> {self.menu_item.name}"
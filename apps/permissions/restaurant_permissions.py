from rest_framework import permissions
from rest_framework.permissions import BasePermission

from apps.core.constants.choices import UserType
from apps.restaurant.models.restaurant import Restaurant


class IsRestaurantOwner(BasePermission):
    """
    Permission to allow only restaurant owners to perform write operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
            request.user.is_authenticated
            and request.user.user_type == UserType.RESTAURANT_OWNER
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        restaurant = getattr(obj, "restaurant", None)

        if not restaurant:
            return False

        return restaurant.owner == request.user


class IsOwnerOrReadOnly(BasePermission):
    """
    Only restaurant owner can update/delete own restaurant.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        return (
            request.user.is_authenticated
            and request.user.user_type == UserType.RESTAURANT_OWNER
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user


class IsMenuItemOwner(BasePermission):
    """
    Only restaurant owner can manage menu items.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not (
            request.user.is_authenticated
            and request.user.user_type == UserType.RESTAURANT_OWNER
        ):
            return False

        if request.method == "POST":
            restaurant_id = request.data.get("restaurant")

            if not restaurant_id:
                return False

            try:
                restaurant = Restaurant.objects.get(id=restaurant_id)
                return restaurant.owner == request.user
            except Restaurant.DoesNotExist:
                return False

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.restaurant.owner == request.user
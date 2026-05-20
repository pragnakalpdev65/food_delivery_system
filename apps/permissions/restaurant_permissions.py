from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages
from apps.core.constants.choices import UserType
from apps.restaurant.models.restaurant import Restaurant
class IsRestaurantOwner(BasePermission):
    """
    Permission to allow only restaurant owners to perform write operations.
    Read-only access is allowed for all users.
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
    Custom permission to only allow restaurant owners to edit or create objects.
    
    This permission checks if the user is authenticated and has 
    the canonical restaurant_owner user type.
    """

    def has_permission(self, request, view):
        """
        Check if the request has the necessary permissions.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and is a restaurant owner, 
                  False otherwise.
        """
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated  

        return (
            request.user.is_authenticated
            and request.user.user_type == UserType.RESTAURANT_OWNER
        )
class IsMenuItemOwner(BasePermission):
    """
    Custom permission to ensure only the restaurant owner can create, modify, 
    or delete menu items for their restaurant.
    
    This permission class checks both:
    1. User is a restaurant owner
    2. User owns the restaurant the menu item belongs to
    """

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and is a restaurant owner.
        
        For read operations, allow all users (authenticated and unauthenticated).
        For create/modify/delete, validate user is a restaurant owner and 
        owns the specified restaurant.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # User must be authenticated and be a restaurant owner
        if not (request.user.is_authenticated 
                and request.user.user_type == UserType.RESTAURANT_OWNER):
            return False
        
        # For create operations, validate restaurant ownership
        if request.method == 'POST':
            restaurant_id = request.data.get('restaurant')
            
            if not restaurant_id:
                return False
            
            try:
                restaurant = Restaurant.objects.get(id=restaurant_id)
                # User must own the restaurant
                return restaurant.owner == request.user
            except Restaurant.DoesNotExist:
                return False
        
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if the user owns the restaurant for this menu item.
        
        Args:
            request: The incoming HTTP request.
            view: The view being accessed.
            obj: The MenuItem object being accessed.
        
        Returns:
            bool: True if user owns the restaurant, False otherwise.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, user must own the restaurant
        return obj.restaurant.owner == request.user

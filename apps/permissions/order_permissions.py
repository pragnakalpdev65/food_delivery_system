from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages
from apps.core.constants.user_types import UserType


class IsCustomerOrReadOnly(BasePermission):
    """
    Allows access only to authenticated customers.
    Note: Despite the 'ReadOnly' name, the current logic restricts all 
    methods to authenticated users with the customer user type.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == UserType.CUSTOMER
        )
                      
class IsRestaurantOwnerOrDriver(BasePermission):
    """
    Object-level permission to allow access only if the user is 
    the owner of the restaurant or the assigned driver for the object.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        return (
            obj.restaurant.owner == user
            or obj.driver == user
        )
           
class IsCustomer(BasePermission):
    """
    Allows access only to authenticated users with a customer user type.
    Uses canonical user type constant for consistency.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == UserType.CUSTOMER 
    
class IsDriver(BasePermission):
    """
    Allows access only to authenticated users with a delivery driver user type.
    Uses canonical user type constant for consistency.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == UserType.DELIVERY_DRIVER 
    
class IsOrderCustomer(BasePermission):
    """
    Object-level permission to ensure the user requesting the order 
    is the customer who placed it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user
    
class IsRestaurantOwner(BasePermission):
    """
    Permission to allow access only to restaurant owners.
    
    'has_permission' checks if the user type matches the restaurant owner canonical value.
    'has_object_permission' ensures the user owns the specific restaurant 
    associated with the object.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == UserType.RESTAURANT_OWNER

    def has_object_permission(self, request, view, obj):
        return obj.restaurant.owner == request.user  

import logging
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages

logger = logging.getLogger(__name__)

class IsCustomerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "Customer"
        )
                      
class IsRestaurantOwnerOrDriver(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        return (
            obj.restaurant.owner == user
            or obj.driver == user
        )
           
class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.user_type == "Customer" or request.user.user_type == "customer") 
    
class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.user_type == "DRIVER" or request.user.user_type == "driver") 
    
class IsOrderCustomer(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user
    
class IsRestaurantOwner(BasePermission):
    def has_permission(self, request, view):
        print(request.user.user_type )
        return request.user.is_authenticated and (request.user.user_type == "Restaurant Owner" or request.user.user_type == "RESTAURANT_OWNER" or request.user.user_type == "restaurant_owner")

    def has_object_permission(self, request, view, obj):
        return obj.restaurant.owner == request.user
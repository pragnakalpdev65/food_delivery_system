import logging
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.messages import AuthMessages

logger = logging.getLogger(__name__)

# class IsOwnerOrReadOnly(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         if request.method in permissions.SAFE_METHODS:
#             return True

#         if obj.owner != request.user:
#             raise PermissionDenied("You are not the owner of this restaurant.")

class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "Restaurant Owner"
        )
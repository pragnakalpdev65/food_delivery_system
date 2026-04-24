from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from apps.permissions.restaurant_permissions import IsOwnerOrReadOnly
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer


class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["category", "dietary_info", "is_available"]
    search_fields = ["name", "description"]
    
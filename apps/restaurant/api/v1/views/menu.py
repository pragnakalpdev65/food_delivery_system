from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from apps.permissions.restaurant_permissions import IsOwnerOrReadOnly
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer, MenuItemDetailSerializer, MenuItemListSerializer
from common.api.pagination import MenuItemPagination

class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.all()
    pagination_class = MenuItemPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "dietary_info", "is_available"]
    search_fields = ["name", "description"]
    ordering_fields = ["price","name","-created_at"]
    
    def get_queryset(self):
        return MenuItem.objects.all().order_by("-created_at")
    
    def get_serializer_class(self):
        if self.action == "list":
            return MenuItemListSerializer  
        elif self.action == "retrieve":
            return MenuItemDetailSerializer  
        return MenuItemSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from apps.permissions.restaurant_permissions import IsMenuItemOwner
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample, OpenApiTypes

from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer, MenuItemDetailSerializer, MenuItemListSerializer
from common.api.pagination import MenuItemPagination
from django.db.models import Count

@extend_schema_view(
    list=extend_schema(
        tags=["Menu"],
        description="Get a paginated list of menu items",
        responses=MenuItemListSerializer(many=True),
    ),
    retrieve=extend_schema(
        tags=["Menu"],
        description="Get detailed information for a single menu item",
        responses=MenuItemDetailSerializer,
    ),
    create=extend_schema(
        tags=["Menu"],
        description="Create a new menu item",
        request=MenuItemSerializer,
        responses=MenuItemSerializer,
        examples=[
            OpenApiExample(
                "Menu Item Example",
                value={
                    "name": "Margherita Pizza",
                    "price": "12.00",
                    "category": "Pizza",
                    "description": "Classic cheese pizza.",
                    "is_available": True,
                },
            )
        ],
    ),
    update=extend_schema(
        tags=["Menu"],
        description="Update a menu item",
        request=MenuItemSerializer,
        responses=MenuItemSerializer,
    ),
    partial_update=extend_schema(
        tags=["Menu"],
        description="Partially update a menu item",
        request=MenuItemSerializer,
        responses=MenuItemSerializer,
    ),
    destroy=extend_schema(
        tags=["Menu"],
        description="Delete a menu item",
        responses=OpenApiTypes.OBJECT,
    ),
)
class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.annotate(
        favorite_count=Count('favorited_by')
    ).order_by('id')

    pagination_class = MenuItemPagination
    permission_classes = [IsMenuItemOwner]

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
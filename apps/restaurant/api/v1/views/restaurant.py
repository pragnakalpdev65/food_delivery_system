from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample
)

from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem

from apps.restaurant.api.v1.serializers.restaurant import (
    RestaurantSerializer,
    RestaurantDetailSerializer,
    RestaurantListSerializer
)
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer

from apps.permissions.restaurant_permissions import IsOwnerOrReadOnly
from common.api.pagination import RestaurantPagination, MenuItemPagination

from apps.restaurant.services.cache_services import RestaurantCacheService


@extend_schema_view(
    list=extend_schema(
        description="Get list of restaurants",
        parameters=[
            OpenApiParameter(name="cuisine_type", description="Filter by cuisine", required=False, type=str),
            OpenApiParameter(name="is_open", description="Filter open restaurants", required=False, type=bool),
            OpenApiParameter(name="search", description="Search by name or cuisine", required=False, type=str),
            OpenApiParameter(name="ordering", description="Order by rating, delivery_fee, created_at", required=False, type=str),
        ],
        responses=RestaurantListSerializer,
        tags=["Restaurants"],
    ),
    retrieve=extend_schema(
        description="Get restaurant details",
        responses=RestaurantDetailSerializer,
        tags=["Restaurants"],
    ),
    create=extend_schema(
        description="Create a new restaurant (Only Owner)",
        request=RestaurantSerializer,
        responses=RestaurantSerializer,
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "name": "Pizza Hub",
                    "cuisine_type": "Italian",
                    "delivery_fee": "50.00",
                    "is_open": True
                },
            )
        ],
        tags=["Restaurants"],
    ),
)
class RestaurantViewSet(ModelViewSet):

    queryset = Restaurant.objects.all().order_by('id') 
    pagination_class = RestaurantPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["cuisine_type", "is_open"]
    search_fields = ["name", "cuisine_type"]
    ordering_fields = ["average_rating", "delivery_fee", "created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]

    def get_serializer_class(self):
        if self.action == "list":
            return RestaurantListSerializer
        elif self.action == "retrieve":
            return RestaurantDetailSerializer
        return RestaurantSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        data = RestaurantCacheService.get_restaurant_list(serializer.data)

        return self.get_paginated_response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        data = RestaurantCacheService.get_restaurant_detail(
            instance.id,
            serializer.data
        )
        return Response(data)

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        RestaurantCacheService.clear_restaurant_list()
        RestaurantCacheService.clear_popular_restaurants()

    def perform_update(self, serializer):
        instance = serializer.save()
        RestaurantCacheService.clear_restaurant_list()
        RestaurantCacheService.clear_restaurant_detail(instance.id)
        RestaurantCacheService.clear_popular_restaurants()

    def perform_destroy(self, instance):
        RestaurantCacheService.clear_restaurant_list()
        RestaurantCacheService.clear_restaurant_detail(instance.id)
        RestaurantCacheService.clear_popular_restaurants()
        instance.delete()

@extend_schema(
        description="Get menu items for a restaurant",
        parameters=[
            OpenApiParameter(
                name="restaurant_id",
                location=OpenApiParameter.PATH,
                description="Restaurant ID",
                required=True,
                type=str,
            )
        ],
        responses=MenuItemSerializer,
        tags=["Menu"],
    )
class RestaurantMenuView(ListAPIView):
    serializer_class = MenuItemSerializer
    pagination_class = MenuItemPagination 

    def get_queryset(self):
        restaurant_id = self.kwargs.get("restaurant_id")
        return MenuItem.objects.filter(restaurant_id=restaurant_id)

    def list(self, request, *args, **kwargs):
        restaurant_id = self.kwargs.get("restaurant_id")

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)

        data = RestaurantCacheService.get_restaurant_menu(
            restaurant_id,
            serializer.data
        )

        return self.get_paginated_response(data)
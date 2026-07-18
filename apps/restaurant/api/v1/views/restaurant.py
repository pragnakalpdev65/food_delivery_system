from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from apps.core.constants.choices import UserType
from apps.order.models.order import Order
from apps.order.api.v1.serializers.orders import OrderSerializer

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
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
from django.db.models import Count 


@extend_schema_view(
    list=extend_schema(
        description="Get a paginated list of restaurants. Supports filtering, search, and ordering.",
        parameters=[
            OpenApiParameter(name="page", description="Page number", required=False, type=int),
            OpenApiParameter(name="page_size", description="Results per page (max 100)", required=False, type=int),
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
    update=extend_schema(
        description="Update an existing restaurant",
        request=RestaurantSerializer,
        responses=RestaurantSerializer,
        tags=["Restaurants"],
    ),
    partial_update=extend_schema(
        description="Partially update an existing restaurant",
        request=RestaurantSerializer,
        responses=RestaurantSerializer,
        tags=["Restaurants"],
    ),
    destroy=extend_schema(
        description="Delete a restaurant",
        responses=OpenApiTypes.OBJECT,
        tags=["Restaurants"],
    ),
)
class RestaurantViewSet(ModelViewSet):

    queryset = Restaurant.objects.all()
    pagination_class = RestaurantPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["cuisine_type", "is_open"]
    search_fields = ["name", "cuisine_type"]
    ordering_fields = ["average_rating", "delivery_fee", "created_at"]
    
    def get_queryset(self):
        queryset = Restaurant.objects.annotate(
            favorite_count=Count("favorited_by")
        )

        if self.action in [
            "update",
            "partial_update",
            "destroy",
        ]:
            return queryset.filter(
                owner=self.request.user
            )

        return queryset.order_by("id")

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
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        data = RestaurantCacheService.get_restaurant_detail(
            instance
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
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        detail_serializer = RestaurantDetailSerializer(
            serializer.instance,
            context={"request": request},
        )
        return Response(detail_serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

@extend_schema(
        description=(
            "Get paginated menu items for a restaurant. "
            "Supports filtering by category, dietary_info, is_available, and search."
        ),
        parameters=[
            OpenApiParameter(
                name="restaurant_id",
                location=OpenApiParameter.PATH,
                description="Restaurant ID",
                required=True,
                type=str,
            ),
            OpenApiParameter(name="page", type=int, required=False, description="Page number"),
            OpenApiParameter(name="page_size", type=int, required=False, description="Results per page (max 100)"),
            OpenApiParameter(name="category", type=str, required=False, description="Filter by category"),
            OpenApiParameter(name="dietary_info", type=str, required=False, description="Filter by dietary info"),
            OpenApiParameter(name="is_available", type=bool, required=False, description="Filter by availability"),
            OpenApiParameter(name="search", type=str, required=False, description="Search name or description"),
            OpenApiParameter(name="ordering", type=str, required=False, description="Order by price, name, or created_at"),
        ],
        responses=MenuItemSerializer(many=True),
        tags=["Menu"],
    )
class RestaurantMenuView(ListAPIView):
    serializer_class = MenuItemSerializer
    pagination_class = MenuItemPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "dietary_info", "is_available"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        restaurant_id = self.kwargs.get("restaurant_id")
        return MenuItem.objects.filter(restaurant_id=restaurant_id)

    def list(self, request, *args, **kwargs):
        restaurant_id = self.kwargs.get("restaurant_id")

        if not Restaurant.objects.filter(id=restaurant_id).exists():
            return Response(
                {"detail": "Restaurant not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return super().list(request, *args, **kwargs)

@extend_schema(
    tags=["Restaurants"],
    description="Get restaurants owned by authenticated restaurant owner",
    responses=RestaurantListSerializer(many=True),
)
class MyRestaurantsView(ListAPIView):
    """
    Return restaurants owned by the authenticated restaurant owner.
    """

    serializer_class = RestaurantListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RestaurantPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Restaurant.objects.none()

        user = self.request.user

        if not user.is_authenticated or user.user_type != UserType.RESTAURANT_OWNER:
            return Restaurant.objects.none()

        return Restaurant.objects.filter(
            owner=user
        ).order_by("-created_at")

@extend_schema(
    tags=["Orders"],
    description="Get paginated orders for restaurants owned by authenticated restaurant owner",
    parameters=[
        OpenApiParameter(
            name="restaurant_id",
            description="Filter orders by restaurant ID",
            required=False,
            type=str,
        ),
        OpenApiParameter(name="page", type=int, required=False, description="Page number"),
        OpenApiParameter(name="page_size", type=int, required=False, description="Results per page"),
    ],
    responses=OrderSerializer(many=True),
)
class RestaurantOrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RestaurantPagination
    queryset = Order.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        user = self.request.user

        if not user.is_authenticated or user.user_type != UserType.RESTAURANT_OWNER:
            return Order.objects.none()

        queryset = Order.objects.filter(
            restaurant__owner=user
        )

        restaurant_id = self.request.query_params.get("restaurant_id")
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)

        return (
            queryset
            .select_related(
                "customer",
                "restaurant",
                "driver"
            )
            .order_by("-created_at")
        )
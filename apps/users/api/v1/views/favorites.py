from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework import permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiTypes, OpenApiParameter

from apps.restaurant.models.restaurant import Restaurant
from apps.users.models import FavoriteRestaurant
from apps.users.api.v1.serializers.favorites import FavoriteRestaurantSerializer
from apps.permissions.order_permissions import IsCustomer
from apps.restaurant.models.menu import MenuItem
from apps.users.models import FavoriteMenuItem
from apps.users.api.v1.serializers.favorites import FavoriteMenuItemSerializer
from apps.core.constants.messages import AuthMessages
from common.api.pagination import FavoritePagination
@extend_schema_view(
    list=extend_schema(
        tags=["Users"],
        description="List favorite restaurants for the authenticated user",
        responses=FavoriteRestaurantSerializer(many=True),
    ),
    create=extend_schema(
        tags=["Users"],
        description="Add a restaurant to favorites",
        request={
            "application/json": {
                "type": "object",
                "properties": {"restaurant_id": {"type": "string"}},
                "required": ["restaurant_id"],
            }
        },
        responses=OpenApiTypes.OBJECT,
    ),
    destroy=extend_schema(
        tags=["Users"],
        description="Remove a restaurant from favorites",
        parameters=[
            OpenApiParameter(
                name="pk",
                description="Restaurant ID",
                required=True,
                type=str,
                location=OpenApiParameter.PATH,
            )
        ],
        responses=OpenApiTypes.OBJECT,
    ),
    check=extend_schema(
        tags=["Users"],
        description="Check if a restaurant is favorited by the authenticated user",
        parameters=[
            OpenApiParameter(
                name="pk",
                description="Restaurant ID",
                required=True,
                type=str,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={
            "type": "object",
            "properties": {
                "is_favorited": {"type": "boolean"}
            },
        },
    ),
)
class FavoriteRestaurantViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    pagination_class = FavoritePagination

    def list(self, request):
        queryset = FavoriteRestaurant.objects.select_related("restaurant").filter(
            customer=request.user
        ).order_by('-created_at')

        serializer = FavoriteRestaurantSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        restaurant_id = request.data.get("restaurant_id")

        if not restaurant_id:
            return Response(
                {"detail": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        restaurant = get_object_or_404(Restaurant, id=restaurant_id)

        favorite, created = FavoriteRestaurant.objects.get_or_create(
            customer=request.user,
            restaurant=restaurant,
        )

        if not created:
            return Response(
                {"detail": AuthMessages.ALREADY_FAVORITE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": AuthMessages.ADDED_TO_FAVORITE},
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, pk=None):
        favorite = get_object_or_404(
            FavoriteRestaurant,
            customer=request.user,
            restaurant_id=pk,
        )
        favorite.delete()

        return Response(
            {"detail": AuthMessages.REMOVED_FROM_FAVORITE},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=True, methods=["get"])
    def check(self, request, pk=None):
        is_favorited = FavoriteRestaurant.objects.filter(
            customer=request.user,
            restaurant_id=pk,
        ).exists()

        return Response({"is_favorited": is_favorited})
@extend_schema_view(
    list=extend_schema(
        tags=["Users"],
        description="List favorite menu items for the authenticated user",
        responses=FavoriteMenuItemSerializer(many=True),
    ),
    create=extend_schema(
        tags=["Users"],
        description="Add a menu item to favorites",
        request={
            "application/json": {
                "type": "object",
                "properties": {"item_id": {"type": "string"}},
                "required": ["item_id"],
            }
        },
        responses=OpenApiTypes.OBJECT,
    ),
    destroy=extend_schema(
        tags=["Users"],
        description="Remove a menu item from favorites",
        parameters=[
            OpenApiParameter(
                name="pk",
                description="Menu item ID",
                required=True,
                type=str,
                location=OpenApiParameter.PATH,
            )
        ],
        responses=OpenApiTypes.OBJECT,
    ),
    check=extend_schema(
        tags=["Users"],
        description="Check if a menu item is favorited by the authenticated user",
        parameters=[
            OpenApiParameter(
                name="pk",
                description="Menu item ID",
                required=True,
                type=str,
                location=OpenApiParameter.PATH,
            )
        ],
        responses={
            "type": "object",
            "properties": {
                "is_favorited": {"type": "boolean"}
            },
        },
    ),
)
class FavoriteMenuItemViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    pagination_class = FavoritePagination

    def _get_item(self, item_id):
        if not item_id:
            return None
        return get_object_or_404(MenuItem, id=item_id)

    @extend_schema(tags=["Users"], description="List favorite menu items")
    def list(self, request):
        queryset = (
            FavoriteMenuItem.objects
            .select_related("menu_item")
            .filter(customer=request.user)
            .order_by("-created_at")
        )
        serializer = FavoriteMenuItemSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Users"], description="Add menu item to favorites")
    def create(self, request):
        item_id = request.data.get("item_id")

        if not item_id:
            return Response(
                {"detail": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = self._get_item(item_id)

        favorite, created = FavoriteMenuItem.objects.get_or_create(
            customer=request.user,
            menu_item=item,
        )

        if not created:
            return Response(
                {"detail": AuthMessages.ALREADY_FAVORITE},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": AuthMessages.ADDED_TO_FAVORITE},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Users"], description="Remove menu item from favorites")
    def destroy(self, request, pk=None):
        favorite = get_object_or_404(
            FavoriteMenuItem,
            customer=request.user,
            menu_item_id=pk,
        )
        favorite.delete()

        return Response(
            {"detail": AuthMessages.REMOVED_FROM_FAVORITE},
            status=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(tags=["Users"], description="Check if menu item is favorite")
    @action(detail=True, methods=["get"])
    def check(self, request, pk=None):
        is_favorited = FavoriteMenuItem.objects.filter(
            customer=request.user,
            menu_item_id=pk,
        ).exists()

        return Response({"is_favorited": is_favorited})
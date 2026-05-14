from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.restaurant import Restaurant
from apps.users.models import (
    FavoriteRestaurant,
    FavoriteMenuItem,
)

from apps.users.api.v1.serializers.favorites import (
    FavoriteRestaurantSerializer,
    FavoriteMenuItemSerializer,
)



class FavoriteRestaurantView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        description="Add restaurant to favorites",
    )
    def post(self, request, restaurant_id):
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)

        favorite, created = FavoriteRestaurant.objects.get_or_create(
                customer=request.user,
                restaurant=restaurant,)

        if not created:
            return Response(
                {"detail": "Restaurant already favorited"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Restaurant added to favorites"},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        description="Remove restaurant from favorites",
    )
    def delete(self, request, restaurant_id):
        favorite = FavoriteRestaurant.objects.filter(
            customer=request.user,
            restaurant_id=restaurant_id,
        )

        if not favorite.exists():
            return Response(
                {"detail": "Favorite restaurant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        favorite.delete()

        return Response(
            {"detail": "Restaurant removed from favorites"},
            status=status.HTTP_204_NO_CONTENT,
        )
        
        
class FavoriteRestaurantListView(ListAPIView):
    serializer_class = FavoriteRestaurantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteRestaurant.objects.select_related(
            "restaurant"
        ).filter(customer=self.request.user)
        
class FavoriteRestaurantCheckView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, restaurant_id):
        is_favorited = FavoriteRestaurant.objects.filter(
            customer=request.user,
            restaurant_id=restaurant_id,
        ).exists()

        return Response(
            {"is_favorited": is_favorited},
            status=status.HTTP_200_OK,
        )
class FavoriteMenuItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, item_id):
        item = get_object_or_404(MenuItem, id=item_id)

        favorite, created = FavoriteMenuItem.objects.get_or_create(
            customer=request.user,
            menu_item=item,
        )

        if not created:
            return Response(
                {"detail": "Menu item already favorited"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Menu item added to favorites"},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, item_id):
        favorite = FavoriteMenuItem.objects.filter(
            customer=request.user,
            menu_item_id=item_id,
        )

        if not favorite.exists():
            return Response(
                {"detail": "Favorite menu item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        favorite.delete()

        return Response(
            {"detail": "Menu item removed from favorites"},
            status=status.HTTP_204_NO_CONTENT,
        )
class FavoriteMenuItemListView(ListAPIView):
    serializer_class = FavoriteMenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteMenuItem.objects.select_related(
            "menu_item"
        ).filter(customer=self.request.user)
        
class FavoriteMenuItemCheckView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, item_id):
        is_favorited = FavoriteMenuItem.objects.filter(
            customer=request.user,
            menu_item_id=item_id,
        ).exists()

        return Response(
            {"is_favorited": is_favorited},
            status=status.HTTP_200_OK,
        )
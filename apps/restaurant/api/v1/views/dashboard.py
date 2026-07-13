from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.constants.choices import UserType
from apps.restaurant.api.v1.serializers.dashboard import RestaurantDashboardSerializer
from apps.restaurant.models.restaurant import Restaurant


@extend_schema(
    tags=["Restaurants"],
    summary="Restaurant owner dashboard",
    description=(
        "Dashboard metrics for a restaurant owned by the authenticated owner: "
        "active orders, daily revenue, new customers, menu items, net revenue, "
        "total orders, average order value, average rating, and analytics pack."
    ),
    parameters=[
        OpenApiParameter(
            name="restaurant_id",
            location=OpenApiParameter.PATH,
            required=True,
            type=str,
            description="Restaurant UUID",
        )
    ],
    responses=RestaurantDashboardSerializer,
)
class RestaurantDashboardView(APIView):
    """
    GET /api/v1/restaurant/restaurants/{restaurant_id}/dashboard/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, restaurant_id):
        if request.user.user_type != UserType.RESTAURANT_OWNER:
            return Response(
                {"detail": "Only restaurant owners can access the dashboard."},
                status=403,
            )

        restaurant = get_object_or_404(
            Restaurant,
            id=restaurant_id,
            owner=request.user,
        )

        serializer = RestaurantDashboardSerializer(restaurant)
        return Response(serializer.data)

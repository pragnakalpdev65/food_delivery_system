from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions.order_permissions import IsRestaurantOwner
from apps.restaurant.models.restaurant import Restaurant


class RestaurantOrderWebSocketInfoSerializer(serializers.Serializer):
    restaurant_id = serializers.UUIDField()
    websocket_path = serializers.CharField()
    websocket_url_template = serializers.CharField()
    auth = serializers.CharField()
    events = serializers.ListField(child=serializers.CharField())
    payload_example = serializers.DictField()


@extend_schema(
    tags=["Orders"],
    summary="Restaurant Order Section WebSocket info",
    description=(
        "Returns connection details for the Restaurant Order Section WebSocket. "
        "Connect with a JWT access token as the `token` query parameter."
    ),
    parameters=[
        OpenApiParameter(
            name="restaurant_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description="Restaurant UUID owned by the authenticated owner",
        )
    ],
    responses={200: RestaurantOrderWebSocketInfoSerializer},
    examples=[
        OpenApiExample(
            "WebSocket Info",
            value={
                "restaurant_id": "11111111-1111-1111-1111-111111111111",
                "websocket_path": "/ws/orders/management/<restaurant_id>/",
                "websocket_url_template": (
                    "ws://<host>/ws/orders/management/<restaurant_id>/?token=<access_token>"
                ),
                "auth": "JWT access token via query param `token`",
                "events": [
                    "connected",
                    "order_created",
                    "status_updated",
                    "driver_assigned",
                ],
                "payload_example": {
                    "event": "status_updated",
                    "order_id": "uuid",
                    "status": "preparing",
                },
            },
        )
    ],
)
class RestaurantOrderWebSocketInfoView(APIView):
    """
    REST discovery endpoint for the Restaurant Order Section WebSocket.

    GET /api/v1/order/restaurants/{restaurant_id}/orders/ws/
    """

    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get(self, request, restaurant_id):
        restaurant = Restaurant.objects.filter(
            id=restaurant_id,
            owner=request.user,
        ).first()

        if not restaurant:
            return Response({"detail": "Restaurant not found."}, status=404)

        path = f"/ws/orders/management/{restaurant_id}/"
        return Response(
            {
                "restaurant_id": str(restaurant_id),
                "websocket_path": path,
                "websocket_url_template": f"ws://<host>{path}?token=<access_token>",
                "auth": "Pass JWT access token as query parameter `token`",
                "events": [
                    "connected",
                    "order_created",
                    "status_updated",
                    "driver_assigned",
                ],
                "payload_example": {
                    "event": "status_updated",
                    "order_id": "uuid",
                    "restaurant_id": str(restaurant_id),
                    "status": "preparing",
                    "previous_status": "confirmed",
                    "order_number": 1001,
                },
            }
        )

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.permissions.order_permissions import IsRestaurantOwner
from apps.restaurant.models.restaurant import Restaurant


@extend_schema(
    tags=["Orders"],
    summary="Restaurant Order Section WebSocket info",
    description=(
        "Returns connection details for the Restaurant Order Section WebSocket. "
        "Connect with a JWT access token as the `token` query parameter."
    ),
    responses={
        200: {
            "type": "object",
            "properties": {
                "websocket_path": {"type": "string"},
                "websocket_url_template": {"type": "string"},
                "auth": {"type": "string"},
                "events": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "payload_example": {"type": "object"},
            },
        }
    },
    examples=[
        OpenApiExample(
            "WebSocket Info",
            value={
                "websocket_path": "/ws/orders/management/<restaurant_id>/",
                "websocket_url_template": (
                    "ws(s)://<host>/ws/orders/management/<restaurant_id>/?token=<access_token>"
                ),
                "auth": "JWT access token via query param `token`",
                "events": [
                    "connected",
                    "order_created",
                    "status_updated",
                    "driver_assigned",
                ],
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
        forwarded_proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        scheme = (
            "wss"
            if request.is_secure() or forwarded_proto.split(",")[0].strip() == "https"
            else "ws"
        )
        return Response(
            {
                "restaurant_id": str(restaurant_id),
                "websocket_path": path,
                "websocket_url_template": (
                    f"{scheme}://<host>{path}?token=<access_token>"
                ),
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

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone

from apps.order.models.order import Order
from apps.order.api.v1.serializers.orders import OrderSerializer
from apps.permissions.order_permissions import IsRestaurantOwnerOrDriver
from apps.core.constants.status import OrderStatus
from drf_spectacular.utils import extend_schema
from apps.core.constants.messages import AuthMessages
from apps.core.constants.error_codes import ErrorCodes

ACTIVE_STATUSES = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.PICKED_UP,
]

@extend_schema(
    tags=["Order Management"],
    description="Real-time order handling for drivers and restaurant owners"
)

class OrderManagementViewSet(ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = Order.objects.select_related(
            'customer', 'restaurant', 'driver'
        ).prefetch_related(
            'items', 'items__menu_item'
        ).filter(status__in=ACTIVE_STATUSES)

        if user.user_type == "CUSTOMER":
            return queryset.filter(customer=user)

        if user.user_type == "RESTAURANT_OWNER":
            return queryset.filter(restaurant__owner=user)

        if user.user_type == "DRIVER":
            return queryset.filter(driver=user)

        return queryset.none()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwnerOrDriver])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Status required"}, status=400)

        current_status = order.status
        allowed = VALID_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            return Response(
                {"error": AuthMessages.INVALID_TRANSITION,
                 "code": ErrorCodes.INVALID_TRANSITIONS},
                
            )
        order.status = new_status
        order.save()

        return Response({
            "message": AuthMessages.UPDATE_ORDER,
            "status": order.status
        })

    @action(detail=True, methods=['get'])
    def eta(self, request, pk=None):
        order = self.get_object()

        if not order.created_at:
            return Response({"error": AuthMessages.INVALID_ORDER}, status=400)

        eta = order.created_at + timezone.timedelta(minutes=30)

        return Response({
            "estimated_delivery_time": eta
        })
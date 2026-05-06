from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.order.models.order import Order
from apps.order.api.v1.serializers.orders import OrderSerializer
from apps.permissions.order_permissions import (
    IsCustomer,
    IsDriver,
    IsRestaurantOwner,
    IsOrderCustomer,
    IsRestaurantOwnerOrDriver,
)
from django.core.cache import cache
from apps.core.constants.cache_keys import CacheKey
from apps.users.models import CustomUser
from drf_spectacular.utils import extend_schema, OpenApiExample

VALID_TRANSITIONS = {
    "PENDING": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PREPARING", "CANCELLED"],
    "PREPARING": ["READY"],
    "READY": ["PICKED_UP"],
    "PICKED_UP": ["DELIVERED"],
    "DELIVERED": [],
    "CANCELLED": [],
}

@extend_schema(
    description="""
WebSocket Endpoints:

ws/orders/{id}/ → real-time order updates  
ws/orders/management/{id}/ → order management  
ws/restaurants/{id}/ → restaurant dashboard  

Events:
- order_created
- status_updated
- driver_assigned
"""
)

class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'restaurant']
    search_fields = ['order_number']
    ordering_fields = ['-created_at', 'total_amount']

    @extend_schema(
        description="Create a new order (Customer only)",
        request=OrderSerializer,
        responses=OrderSerializer,
        examples=[
            OpenApiExample(
                "Create Order Example",
                value={
                    "restaurant": "uuid",
                    "delivery_address": "123 Main Street",
                    "items": [
                        {
                            "menu_item": "uuid",
                            "quantity": 2
                        }
                    ]
                },
            )
        ],
    )

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related(
            'customer', 'restaurant', 'driver'
        ).prefetch_related(
            'items', 'items__menu_item'
        )

        if (user.user_type == "CUSTOMER" or user.user_type == "customer"):
           
            return queryset.filter(customer=user)

        if user.user_type == "RESTAURANT_OWNER":
            return queryset.filter(restaurant__owner=user)

        if user.user_type == "DRIVER":
            return (
                queryset.filter(driver=user)
                | queryset.filter(status__in=["READY", "PENDING", "CONFIRMED"])
            )

        return queryset.none()

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsCustomer()]

        if self.action == "cancel":
            return [IsAuthenticated(), IsOrderCustomer()]

        if self.action == "assign_driver":
            return [IsAuthenticated(), IsRestaurantOwner()]
        
        if self.action == "update_status":
            return [IsAuthenticated(), IsRestaurantOwnerOrDriver()]

        return [IsAuthenticated()]

    @extend_schema(
        description="Cancel an order (Customer only, if pending/confirmed)",
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()

        if order.status == "CANCELLED":
            return Response({"message": "Order is already cancelled"})

        else :
            if order.status not in ["pending", "confirmed","PENDING","CONFIRMED"]:
                return Response(
                    {"error": "Order cannot be cancelled at this stage"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = "CANCELLED"
            order.save()

            return Response({"message": "Order cancelled successfully"})
            

    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        order = self.get_object()
        driver_id = request.data.get("driver_id")

        if not driver_id:
            return Response(
                {"error": "driver_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            driver = CustomUser.objects.get(id=driver_id, user_type="DRIVER")
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Invalid driver"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.driver:
            return Response(
                {"error": "Driver already assigned"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if order.status != "READY":
            return Response(
                {"error": "Order must be READY before assigning driver"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.driver = driver
        order.status = "PICKED_UP"
        order.save()

        return Response({"message": "Driver assigned successfully"})
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "Status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        current_status = order.status

        allowed = VALID_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            return Response(
                {
                    "error": f"Invalid transition from {current_status} to {new_status}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        return Response(
            {
                "message": "Order status updated successfully",
                "status": order.status
            }
        )
        
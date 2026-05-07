from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
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
from apps.core.constants.messages import AuthMessages
from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.user_types import UserType
from apps.users.models import CustomUser
from drf_spectacular.utils import extend_schema, OpenApiExample
from apps.core.constants.status import OrderStatus


VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
    OrderStatus.PREPARING: [OrderStatus.READY],
    OrderStatus.READY: [OrderStatus.PICKED_UP],
    OrderStatus.PICKED_UP: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
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
        user_type = user.user_type
        queryset = Order.objects.select_related(
            'customer', 'restaurant', 'driver'
        ).prefetch_related(
            'items', 'items__menu_item'
        )

        if user_type == UserType.CUSTOMER:
            return queryset.filter(customer=user)

        if user_type == UserType.RESTAURANT_OWNER:
            return queryset.filter(restaurant__owner=user)

        if user_type == UserType.DELIVERY_DRIVER:
            return (
                queryset.filter(driver=user)
                | queryset.filter(status__in=[OrderStatus.READY, OrderStatus.PENDING,OrderStatus.CONFIRMED])
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

        if order.status == OrderStatus.CANCELLED:
            return Response({"message": AuthMessages.ALREADY_CANCELLED})

        else :
            if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:                
                return Response(
                    {"error": AuthMessages.CAN_NOT_BE_CANCELLED,
                    "code" : ErrorCodes.CAN_NOT_BE_CANCELLED},
                   
                )

            order.status = OrderStatus.CANCELLED
            order.save()

            return Response({"message": AuthMessages.CANCELLED_SUCCESS})
            

    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        order = self.get_object()
        driver_id = request.data.get("driver_id")

        if not driver_id:
            return Response(
                {"error":AuthMessages.DRIVER_REQUIRED,
                  "code" : ErrorCodes.DRIVER_REQUIRED},
               
            )

        driver = CustomUser.objects.filter(id=driver_id).first()
        normalized_driver_type = (
            driver.user_type.strip().lower().replace(" ", "_")
        ) if driver else None

        if not driver or normalized_driver_type not in ("driver", "delivery_driver"):
            return Response(
                {"error":AuthMessages.DRIVER_NOT_FOUND,
                 "code" : ErrorCodes.DRIVER_NOT_FOUND},
                
            )

        if order.driver:
            return Response(
                {"error": AuthMessages.ALREADY_ASSIGNED,
                 "code" : ErrorCodes.ALREADY_ASSIGNED},
                
            )

        if order.status != OrderStatus.READY:           
            return Response(
                {"error": AuthMessages.MUST_BE_READY,
                  "code" : ErrorCodes.MUST_BE_READY},
               
            )

        order.driver = driver
        order.status = OrderStatus.PICKED_UP
        order.save()

        return Response({"message":AuthMessages.ASSIGN_SUCCESS })
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error":AuthMessages.STATUS_REQUIRED },
                status=status.HTTP_400_BAD_REQUEST
            )

        current_status = order.status

        allowed = VALID_TRANSITIONS.get(current_status, [])

        if new_status not in allowed:
            return Response(
                {
                    "error": AuthMessages.INVALID_TRANSITION % {
                                "current_status": current_status,
                                "new_status": new_status,
                                },
                    "code" : ErrorCodes.INVALID_TRANSITIONS
                },
                
            )

        order.status = new_status
        order.save()

        return Response(
            {
                "message": AuthMessages.STATUS_UPDATE_SUCCESS,
                "status": order.status
            }
        )
        
    @action(detail=True, methods=['get'])
    def eta(self, request, pk=None):
        order = self.get_object()
        if not order.created_at:
            return Response({"error": AuthMessages.INVALID_ORDER}, status=400)

        eta = order.created_at + timezone.timedelta(minutes=30)

        return Response({
            "estimated_delivery_time": eta
        })
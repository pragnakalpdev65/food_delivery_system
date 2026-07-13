from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.order.models.order import Order
from apps.order.api.v1.serializers.orders import OrderSerializer
from apps.order.api.v1.serializers.reorder import ReorderSerializer
from apps.permissions.order_permissions import (
    IsCustomer,
    IsDriver,
    IsRestaurantOwner,
    IsOrderCustomer,
    IsRestaurantOwnerOrDriver,
)
from django.core.cache import cache
from apps.core.constants.messages import AuthMessages
from apps.restaurant.services.availability_service import RestaurantAvailabilityService
from apps.core.constants.error_codes import ErrorCodes
from apps.core.constants.choices import UserType
from apps.users.models import CustomUser
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiTypes, OpenApiParameter
from apps.core.constants.choices import OrderStatus
from apps.order.services.websocket_services import WebSocketService
from common.api.filters.order_filters import OrderFilter
from common.api.pagination import OrderPagination
from common.api.swagger import (
    AssignDriverRequestSerializer,
    AssignDriverResponseSerializer,
    UpdateOrderStatusRequestSerializer,
    UpdateOrderStatusResponseSerializer,
    OrderETAResponseSerializer,
)
from django.utils import timezone

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
    tags=["Orders"],
    description="""
WebSocket Endpoints (JWT via ?token=<access_token>):

Restaurant Order Section:
  ws/orders/management/{restaurant_id}/
  Events: order_created, status_updated, driver_assigned, connected

Single order tracking:
  ws/orders/{order_id}/

Restaurant dashboard (new orders):
  ws/restaurants/{restaurant_id}/
"""
)
@extend_schema_view(
    list=extend_schema(
        tags=["Orders"],
        description=(
            "List orders visible to the authenticated user. "
            "Supports pagination (?page, ?page_size), filtering, and search."
        ),
        parameters=[
            OpenApiParameter(name="page", type=int, required=False, description="Page number"),
            OpenApiParameter(name="page_size", type=int, required=False, description="Results per page (max 100)"),
            OpenApiParameter(name="status", type=str, required=False, description="Filter by order status"),
            OpenApiParameter(name="restaurant", type=str, required=False, description="Filter by restaurant UUID"),
            OpenApiParameter(name="search", type=str, required=False, description="Search order number or restaurant name"),
        ],
        responses=OrderSerializer(many=True),
    ),
    retrieve=extend_schema(
        tags=["Orders"],
        description="Retrieve a specific order",
        responses=OrderSerializer,
    ),
    update=extend_schema(
        tags=["Orders"],
        description="Update an order",
        request=OrderSerializer,
        responses=OrderSerializer,
    ),
    partial_update=extend_schema(
        tags=["Orders"],
        description="Partially update an order",
        request=OrderSerializer,
        responses=OrderSerializer,
    ),
    destroy=extend_schema(
        tags=["Orders"],
        description="Delete an order",
        responses=OpenApiTypes.OBJECT,
    ),
)
class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OrderFilter

    search_fields = ['order_number','restaurant__name']

    ordering_fields = ['created_at','total_amount','status']

    ordering = ['-created_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

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
        if self.action == "assign_driver":
            return [IsAuthenticated(), IsRestaurantOwner()]
        
        if self.action == "update_status":
            return [IsAuthenticated(), IsRestaurantOwnerOrDriver()]

        return [IsAuthenticated()]

    @extend_schema(
        tags=["Orders"],
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
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        restaurant = serializer.validated_data.get("restaurant")

        is_reorder = getattr(serializer, "is_reorder", False)

        if restaurant and not is_reorder:
            if not RestaurantAvailabilityService.is_currently_open(restaurant.id):
                return Response(
                    {"error": AuthMessages.RESTAURANT_CLOSED},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        tags=["Orders"],
        summary="Assign driver",
        description="Assign a driver to the order (Restaurant owner only). Order must be ready.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Order UUID",
            )
        ],
        request=AssignDriverRequestSerializer,
        responses={200: AssignDriverResponseSerializer},
    )
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
        if driver.user_type != UserType.DELIVERY_DRIVER :
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

        previous_status = order.status
        order.driver = driver
        order.status = OrderStatus.PICKED_UP
        order.save(update_fields=["driver", "status", "updated_at"])

        WebSocketService.notify_driver_assigned(order)
        WebSocketService.notify_status_updated(
            order, previous_status=previous_status
        )

        return Response({"message":AuthMessages.ASSIGN_SUCCESS })

    @extend_schema(
        tags=["Orders"],
        summary="Update order status",
        description="Update order status based on allowed transitions (owner or assigned driver).",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Order UUID",
            )
        ],
        request=UpdateOrderStatusRequestSerializer,
        responses={200: UpdateOrderStatusResponseSerializer},
    )    
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

        previous_status = current_status
        order.status = new_status

        if new_status == OrderStatus.DELIVERED:
            order.actual_delivery_time = timezone.now()
            order.save(update_fields=["status", "actual_delivery_time", "updated_at"])
        else:
            order.save(update_fields=["status", "updated_at"])

        WebSocketService.notify_status_updated(order, previous_status=previous_status)

        return Response(
            {
                "message": AuthMessages.STATUS_UPDATE_SUCCESS,
                "status": order.status
            }
        )
     
    @extend_schema(
        tags=["Orders"],
        summary="Get order ETA",
        description="Get estimated delivery time for the order",
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="Order UUID",
            )
        ],
        responses={200: OrderETAResponseSerializer},
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
    
    @extend_schema(
        tags=["Orders"],
        description="Reorder from a previous order",
        responses=ReorderSerializer
    )
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        original_order = self.get_object()

        serializer = ReorderSerializer(
            data={},
            context={
                "request": request,
                "order": original_order
            }
        )

        serializer.is_valid(raise_exception=True)

        order_data = serializer.save()

        return Response(
            order_data,
            status=status.HTTP_201_CREATED
        )
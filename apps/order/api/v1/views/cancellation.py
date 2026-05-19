from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.order.services.cancellation_services import CancellationServices
from apps.order.models.cancellation import OrderCancellation, CancellationPolicy
from apps.order.api.v1.serializers.cancellation import CancellationPolicySerializer
from django.shortcuts import get_object_or_404
from apps.order.models import Order
from rest_framework.generics import RetrieveUpdateAPIView
from apps.permissions.restaurant_permissions import IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from apps.restaurant.models.restaurant import Restaurant
from apps.permissions.order_permissions import IsCustomer
from apps.core.constants.messages import AuthMessages
from apps.core.constants.choices import OrderStatus

class CancellationView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    @extend_schema(
        description="Cancel an order and get refund details",
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="ID of the order to cancel",
            )
        ],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "reason_detail": {"type": "string"},
                },
                "required": ["reason"],
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "refund_amount": {"type": "number"},
                    "refund_percentage": {"type": "number"},
                    "refund_method": {"type": "string"},
                },
            }
        },
    )
    def post(self, request, order_id=None):
        order = get_object_or_404(Order, id=order_id)
        user = request.user

        reason = request.data.get("reason")
        reason_detail = request.data.get("reason_detail")

        if not reason:
            return Response(
                {"error": AuthMessages.CANCELLATION_REASON_REQUIRED},
                status=400,
            )

        can_cancel, message = CancellationServices.can_cancel(order, user)

        if not can_cancel:
            return Response({"error": message}, status=400)

        refund_amount, refund_percentage = CancellationServices.calculate_refund(order)

        OrderCancellation.objects.create(
            order=order,
            cancelled_by=user,
            reason=reason,
            reason_detail=reason_detail,
            refund_amount=refund_amount,
            refund_percentage=refund_percentage,            
        )
        
        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status"])
        
        return Response({
            "message": AuthMessages.CANCELLED_SUCCESS,
            "refund_amount": refund_amount,
            "refund_percentage": refund_percentage,
            "refund_method": "original_payment_method",            
        })


    @extend_schema(
        description="Check if an order can be cancelled and preview refund details",
        parameters=[
            OpenApiParameter(
                name="order_id",
                type=str,
                location=OpenApiParameter.PATH,
                description="ID of the order",
            )
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "can_cancel": {"type": "boolean"},
                    "message": {"type": "string"},
                    "refund_amount": {"type": "number"},
                    "refund_percentage": {"type": "number"},
                },
            }
        },
    )
    def get(self, request, order_id=None):
        order = get_object_or_404(Order, id=order_id)
        
        refund_amount, refund_percentage = CancellationServices.calculate_refund(order)
        can_cancel, message = CancellationServices.can_cancel(order, request.user)

        return Response({
            "can_cancel": can_cancel,
            "message": message,
            "refund_amount": refund_amount,
            "refund_percentage": refund_percentage
        })

@extend_schema(
    description="Retrieve or update cancellation policy for a restaurant",
    parameters=[
        OpenApiParameter(
            name="restaurant_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="ID of the restaurant",
        )
    ],
    responses=CancellationPolicySerializer,
)
class CancellationPolicyView(RetrieveUpdateAPIView):
    serializer_class = CancellationPolicySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]


    def get_object(self):
        restaurant = get_object_or_404(
            Restaurant,
            id=self.kwargs["restaurant_id"],
            owner=self.request.user, 
        )

        policy, _ = CancellationPolicy.objects.get_or_create(
            restaurant=restaurant
        )
        return policy

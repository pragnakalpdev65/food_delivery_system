from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.order.services.cancellation_services import CancellationServices
from apps.order.models.cancellation import OrderCancellation, CancellationPolicy
from apps.order.api.v1.serializers.cancellation import CancellationPolicySerializer
from django.shortcuts import get_object_or_404
from apps.order.models import Order 
from rest_framework.generics import RetrieveUpdateAPIView
from apps.permissions.restaurant_permissions import IsRestaurantOwner,IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated
from apps.restaurant.models.restaurant import Restaurant

class CancellationView(APIView):
    
    def post(self, request, order_id=None):
        order = get_object_or_404(Order, id=order_id)
        user = request.user
        
        reason = request.data.get("reason")
        reason_detail = request.data.get("reason_detail")
        
        if not reason:
            return Response(
                {"error":"Cancellation reason is required"},
                status=400
                )
        
        can_cancel, message = CancellationServices.can_cancel(order,user)
            
        if not can_cancel:
            return Response({"error":message},status=400)
        
        refund_amount, refund_percentage = CancellationServices.calculate_refund(order)
        
        cancellation = OrderCancellation.objects.create(
            order=order,
            cancelled_by=user,
            reason = reason,
            reason_detail=reason_detail,
            refund_amount=refund_amount,
            refund_percentage=refund_percentage,            
            
        )
        
        order.status = "cancelled"
        order.save(update_fields=["status"])
        
        return Response({
            "message":"Order Cancel successfully",
            "refund_amount":refund_amount,
            "refund_percentage":refund_percentage,
            "refund_method": "original_payment_method",            
        })

    def get(self,request,order_id=None):
        order = get_object_or_404(Order,id=order_id)
        
        refund_amount, refund_percentage = CancellationServices.calculate_refund(order)

        can_cancel, message = CancellationServices.can_cancel(order, request.user)

        return Response({
            "can_cancel": can_cancel,
            "message": message,
            "refund_amount": refund_amount,
            "refund_percentage": refund_percentage
        })

class CancellationPolicyView(RetrieveUpdateAPIView):
    serializer_class = CancellationPolicySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        restaurant = Restaurant.objects.get(
            id=self.kwargs["restaurant_id"],
        )

        policy, _ = CancellationPolicy.objects.get_or_create(
            restaurant=restaurant
        )
        return policy
   
    
    
        
    

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.order.models.order import Order, OrderRating
from apps.order.api.v1.serializers.rating import (
    OrderRatingSerializer
)
from django.core.exceptions import PermissionDenied

class CreateOrderRatingView(generics.CreateAPIView):

    serializer_class = OrderRatingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        order = get_object_or_404(Order,id=self.kwargs["order_id"])

        serializer = self.get_serializer(
            data={
                **request.data,
                "order": order.id,
            },
            context={
                "request": request
            }
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()


        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class RetrieveOrderRatingView(generics.RetrieveAPIView):

    serializer_class = OrderRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):

        order = get_object_or_404(Order,id=self.kwargs["order_id"])

        return get_object_or_404(OrderRating,order=order)


class UpdateOrderRatingView(generics.UpdateAPIView):

    serializer_class = OrderRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):

        order = get_object_or_404(Order,id=self.kwargs["order_id"])

        rating = get_object_or_404(OrderRating,order=order)

        if rating.customer != self.request.user:
            raise PermissionDenied(
                "You can only edit your own rating."
            )

        return rating

class MyRatingsView(generics.ListAPIView):

    serializer_class = OrderRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return OrderRating.objects.filter(
            customer=self.request.user
        ).select_related(
            "order",
            "order__restaurant"
        ).order_by("-created_at")
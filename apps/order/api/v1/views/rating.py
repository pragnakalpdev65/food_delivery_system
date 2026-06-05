from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.order.models.order import Order, OrderRating
from apps.order.api.v1.serializers.rating import OrderRatingSerializer
from django.core.exceptions import PermissionDenied
from apps.core.constants.messages import AuthMessages
from common.api.pagination import MyRatingsPagination

@extend_schema(
    tags=["Orders"],
    description="Create a rating for a specific order",
    request=OrderRatingSerializer,
    responses=OrderRatingSerializer,
    parameters=[
        OpenApiParameter(
            name="order_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="ID of the order to rate",
        )
    ],
)
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
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Orders"],
    description="Retrieve or update your rating for a specific order",
    request=OrderRatingSerializer,
    responses=OrderRatingSerializer,
    parameters=[
        OpenApiParameter(
            name="order_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="ID of the order",
        )
    ],
)
class OrderRatingDetailView(generics.RetrieveUpdateAPIView):
    """Handles GET and PUT/PATCH for an order rating."""

    serializer_class = OrderRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        order = get_object_or_404(Order, id=self.kwargs["order_id"])
        return get_object_or_404(OrderRating, order=order)

    def update(self, request, *args, **kwargs):
        rating = self.get_object()

        if rating.customer != request.user:
            raise PermissionDenied(AuthMessages.EDIT_RATING_PERMISSIONS)
        return super().update(request, *args, **kwargs)
@extend_schema(
    tags=["Orders"],
    description="List all ratings created by the authenticated user",
    responses=OrderRatingSerializer(many=True),
)
class MyRatingsView(generics.ListAPIView):
    serializer_class = OrderRatingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MyRatingsPagination

    def get_queryset(self):
        return (
            OrderRating.objects.filter(customer=self.request.user)
            .select_related("order", "order__restaurant")
            .order_by("-created_at")
        )
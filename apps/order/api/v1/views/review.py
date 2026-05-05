from rest_framework.views import View,APIView
from apps.order.api.v1.serializers.review import ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from common.api.pagination import ReviewPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.order.models.order import Review
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.generics import ListCreateAPIView

@extend_schema(
    description="Create review for delivered order (Customer only)",
    request=ReviewSerializer,
    responses=ReviewSerializer,
    examples=[
        OpenApiExample(
            "Review Example",
            value={
                "order": "uuid",
                "restaurant": "uuid",
                "menu_item": "uuid",
                "rating": 5,
                "comment": "Great food!"
            },
        )
    ],
)

class ReviewView(ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.all()

    pagination_class = ReviewPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['rating', 'restaurant', 'menu_item']
    ordering_fields = ['created_at', 'rating']
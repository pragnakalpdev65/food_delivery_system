from apps.order.api.v1.serializers.review import ReviewSerializer
from rest_framework.permissions import IsAuthenticated
from common.api.pagination import ReviewPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from apps.order.models.order import Review
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from rest_framework.generics import ListCreateAPIView


@extend_schema_view(
    get=extend_schema(
        tags=["Orders"],
        summary="List reviews",
        description="List reviews with optional filters",
        parameters=[
            OpenApiParameter(name="rating", type=int, required=False, description="Filter by rating"),
            OpenApiParameter(name="restaurant", type=str, required=False, description="Filter by restaurant UUID"),
            OpenApiParameter(name="menu_item", type=str, required=False, description="Filter by menu item UUID"),
            OpenApiParameter(name="ordering", type=str, required=False, description="Order by created_at or rating"),
            OpenApiParameter(name="limit", type=int, required=False, description="Page size (limit/offset)"),
            OpenApiParameter(name="offset", type=int, required=False, description="Offset for pagination"),
        ],
        responses=ReviewSerializer(many=True),
    ),
    post=extend_schema(
        tags=["Orders"],
        summary="Create review",
        description="Create review for a delivered order (Customer only)",
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
                    "comment": "Great food!",
                },
            )
        ],
    ),
)
class ReviewView(ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.all()

    pagination_class = ReviewPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["rating", "restaurant", "menu_item"]
    ordering_fields = ["created_at", "rating"]

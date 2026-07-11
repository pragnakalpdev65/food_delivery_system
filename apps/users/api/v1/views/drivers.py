from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.core.constants.choices import UserType
from apps.permissions.order_permissions import IsRestaurantOwner
from apps.users.api.v1.serializers.profile import DriverListSerializer
from apps.users.models.profile import DriverProfile
from common.api.pagination import StandardPagination


@extend_schema(
    tags=["Users"],
    summary="List drivers",
    description=(
        "List active delivery drivers for order assignment. "
        "Restaurant owners only. Optional filter: is_available."
    ),
    parameters=[
        OpenApiParameter(
            name="is_available",
            type=bool,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filter by driver availability",
        ),
    ],
    responses=DriverListSerializer(many=True),
)
class DriverListView(ListAPIView):
    """
    GET /api/v1/users/drivers/

    Returns drivers that restaurant owners can assign to ready orders.
    Use `driver_id` from each result with assign_driver.
    """

    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    serializer_class = DriverListSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_available"]

    def get_queryset(self):
        return (
            DriverProfile.objects.select_related("user")
            .filter(
                user__user_type=UserType.DELIVERY_DRIVER,
                user__is_active=True,
            )
            .order_by("-is_available", "user__username")
        )

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.operating_hours import (
    OperatingHours,
    SpecialHours
)
from apps.restaurant.api.v1.serializers.operating_hours import (
    OperatingHoursSerializer,
    SpecialHoursSerializer,
    RestaurantAvailabilitySerializer
)
from apps.restaurant.services.availability_service import RestaurantAvailabilityService
from apps.permissions.restaurant_permissions import IsRestaurantOwner
from django.shortcuts import get_object_or_404


def _uuid_pk_param(name="pk", description="Restaurant UUID"):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.UUID,
        location=OpenApiParameter.PATH,
        description=description,
    )


@extend_schema_view(
    get=extend_schema(
        tags=["Restaurants"],
        summary="List operating hours",
        description="List operating hours for a restaurant (owner only)",
        parameters=[_uuid_pk_param()],
        responses={200: OperatingHoursSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Restaurants"],
        summary="Create operating hours",
        description="Create operating hours for a restaurant (owner only)",
        parameters=[_uuid_pk_param()],
        request=OperatingHoursSerializer,
        responses={201: OperatingHoursSerializer},
    ),
)
class OperatingHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = OperatingHoursSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    queryset = OperatingHours.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OperatingHours.objects.none()
        return OperatingHours.objects.filter(
            restaurant_id=self.kwargs["pk"],
            restaurant__owner=self.request.user,
        )

    def perform_create(self, serializer):
        restaurant = get_object_or_404(
            Restaurant,
            pk=self.kwargs["pk"],
            owner=self.request.user,
        )
        serializer.save(restaurant=restaurant)


@extend_schema(
    tags=["Restaurants"],
    summary="Update operating hours",
    description="Update operating hours for a restaurant day",
    parameters=[
        _uuid_pk_param(),
        OpenApiParameter(
            name="day",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="Day of week (0=Monday … 6=Sunday)",
        ),
    ],
    request=OperatingHoursSerializer,
    responses={200: OperatingHoursSerializer},
)
class OperatingHoursUpdateView(generics.UpdateAPIView):

    serializer_class = OperatingHoursSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    lookup_field = "day_of_week"
    lookup_url_kwarg = "day"
    queryset = OperatingHours.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OperatingHours.objects.none()
        return OperatingHours.objects.filter(
            restaurant_id=self.kwargs["pk"]
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Restaurants"],
        summary="List special hours",
        description="List special hours for a restaurant (owner only)",
        parameters=[_uuid_pk_param()],
        responses={200: SpecialHoursSerializer(many=True)},
    ),
    post=extend_schema(
        tags=["Restaurants"],
        summary="Create special hours",
        description="Create special hours for a restaurant (owner only)",
        parameters=[_uuid_pk_param()],
        request=SpecialHoursSerializer,
        responses={201: SpecialHoursSerializer},
    ),
)
class SpecialHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = SpecialHoursSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    queryset = SpecialHours.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SpecialHours.objects.none()
        return SpecialHours.objects.filter(
            restaurant_id=self.kwargs["pk"],
            restaurant__owner=self.request.user,
        )

    def perform_create(self, serializer):
        restaurant = get_object_or_404(
            Restaurant,
            pk=self.kwargs["pk"],
            owner=self.request.user,
        )
        serializer.save(restaurant=restaurant)


@extend_schema(
    tags=["Restaurants"],
    summary="Delete special hours",
    description="Delete a special hours entry for a restaurant",
    parameters=[
        _uuid_pk_param(),
        OpenApiParameter(
            name="special_hours_id",
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description="Special hours UUID",
        ),
    ],
    responses={204: None},
)
class SpecialHoursDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    lookup_field = "id"
    lookup_url_kwarg = "special_hours_id"
    queryset = SpecialHours.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SpecialHours.objects.none()
        return SpecialHours.objects.filter(
            restaurant_id=self.kwargs["pk"],
            restaurant__owner=self.request.user,
        )


@extend_schema(
    tags=["Restaurants"],
    summary="Check if restaurant is open",
    description="Check whether a restaurant is currently open",
    auth=[],
    parameters=[_uuid_pk_param()],
    responses={200: RestaurantAvailabilitySerializer},
)
class RestaurantIsOpenView(generics.GenericAPIView):

    serializer_class = RestaurantAvailabilitySerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        restaurant_id = self.kwargs["pk"]
        is_open = RestaurantAvailabilityService.is_currently_open(restaurant_id)
        data = {
            "restaurant_id": restaurant_id,
            "is_open": is_open,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)


@extend_schema(
    tags=["Restaurants"],
    summary="Next opening time",
    description="Get the next opening time for a restaurant",
    auth=[],
    parameters=[_uuid_pk_param()],
    responses={200: RestaurantAvailabilitySerializer},
)
class RestaurantNextOpeningView(generics.GenericAPIView):

    serializer_class = RestaurantAvailabilitySerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        restaurant_id = self.kwargs["pk"]
        next_opening = RestaurantAvailabilityService.get_next_opening_time(restaurant_id)
        data = {
            "restaurant_id": restaurant_id,
            "next_opening_time": next_opening,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

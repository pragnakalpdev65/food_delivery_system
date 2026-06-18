from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiTypes
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


@extend_schema(
    tags=["Restaurants"],
    description="List and create operating hours for a restaurant",
    request=OperatingHoursSerializer,
    responses=OperatingHoursSerializer(many=True),
)
class OperatingHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = OperatingHoursSerializer
    permission_classes = [IsAuthenticated,IsRestaurantOwner]
        
    # def get_queryset(self):
    #     return OperatingHours.objects.filter(
    #         restaurant_id=self.kwargs['pk']
    #     )
    
    def get_queryset(self):
        return OperatingHours.objects.filter(
            restaurant_id=self.kwargs["pk"],
            restaurant__owner=self.request.user,
        )

    def perform_create(self, serializer):

        restaurant = get_object_or_404(
            Restaurant,
            pk=self.kwargs['pk'],
            owner=self.request.user
        )
        serializer.save(restaurant=restaurant)


@extend_schema(
    tags=["Restaurants"],
    description="Update operating hours for a restaurant",
    request=OperatingHoursSerializer,
    responses=OperatingHoursSerializer,
)
class OperatingHoursUpdateView(generics.UpdateAPIView):

    serializer_class = OperatingHoursSerializer
    permission_classes = [IsAuthenticated,IsRestaurantOwner]
    lookup_field = 'day_of_week'
    lookup_url_kwarg = 'day'

    def get_queryset(self):
        
        return OperatingHours.objects.filter(
            restaurant_id=self.kwargs['pk']
        )

@extend_schema(
    tags=["Restaurants"],
    description="List and create special hours for a restaurant",
    request=SpecialHoursSerializer,
    responses=SpecialHoursSerializer(many=True),
)
class SpecialHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = SpecialHoursSerializer
    permission_classes = [IsAuthenticated,IsRestaurantOwner]

    # def get_queryset(self):

    #     return SpecialHours.objects.filter(
    #         restaurant_id=self.kwargs['pk']
    #     )
    
    def get_queryset(self):
        return SpecialHours.objects.filter(
            restaurant_id=self.kwargs["pk"],
            restaurant__owner=self.request.user,
        )

    def perform_create(self, serializer):

        restaurant = get_object_or_404(
            Restaurant,
            pk=self.kwargs['pk'],
            owner=self.request.user
        )
        serializer.save(restaurant=restaurant)


@extend_schema(
    tags=["Restaurants"],
    description="Delete a special hours entry for a restaurant",
    responses=OpenApiTypes.OBJECT,
)
class SpecialHoursDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated,IsRestaurantOwner]
    lookup_field = 'id'  
    lookup_url_kwarg = 'special_hours_id'

    # def get_queryset(self):

    #     return SpecialHours.objects.filter(
    #         restaurant_id=self.kwargs['pk']
    #     )
    
    def get_queryset(self):
        return SpecialHours.objects.filter(
            restaurant_id=self.kwargs["pk"],
            restaurant__owner=self.request.user,
        )


@extend_schema(
    tags=["Restaurants"],
    description="Check whether a restaurant is currently open",
    responses=RestaurantAvailabilitySerializer,
)
class RestaurantIsOpenView(generics.GenericAPIView):

    serializer_class = RestaurantAvailabilitySerializer
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):

        restaurant_id = self.kwargs['pk']

        is_open = (
            RestaurantAvailabilityService
            .is_currently_open(restaurant_id)
        )
        data = {
            'restaurant_id': restaurant_id,
            'is_open': is_open,
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)

@extend_schema(
    tags=["Restaurants"],
    description="Get the next opening time for a restaurant",
    responses=RestaurantAvailabilitySerializer,
)
class RestaurantNextOpeningView(generics.GenericAPIView):

    serializer_class = RestaurantAvailabilitySerializer
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):

        restaurant_id = self.kwargs['pk']

        next_opening = RestaurantAvailabilityService.get_next_opening_time(restaurant_id)

        data = {
            'restaurant_id': restaurant_id,
            'next_opening_time': next_opening,
        }

        serializer = self.get_serializer(data)

        return Response(serializer.data)
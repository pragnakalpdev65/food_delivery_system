from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

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
from apps.restaurant.services.availability_service import (
    RestaurantAvailabilityService
)
from apps.permissions.restaurant_permissions import IsRestaurantOwner


class OperatingHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = OperatingHoursSerializer
    permission_classes = [IsAuthenticated,IsRestaurantOwner]

    def get_queryset(self):

        return OperatingHours.objects.filter(
            restaurant_id=self.kwargs['pk']
        )

    def perform_create(self, serializer):

        restaurant = Restaurant.objects.get(pk=self.kwargs['pk'])

        serializer.save(restaurant=restaurant)


class OperatingHoursUpdateView(generics.UpdateAPIView):

    serializer_class = OperatingHoursSerializer
    permission_classes = [IsAuthenticated,IsRestaurantOwner]
    lookup_field = 'day_of_week'
    lookup_url_kwarg = 'day'

    def get_queryset(self):
        
        return OperatingHours.objects.filter(
            restaurant_id=self.kwargs['pk']
        )

class SpecialHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = SpecialHoursSerializer
    permission_classes = [IsAuthenticated,IsRestaurantOwner]

    def get_queryset(self):

        return SpecialHours.objects.filter(
            restaurant_id=self.kwargs['pk']
        )

    def perform_create(self, serializer):

        restaurant = Restaurant.objects.get(pk=self.kwargs['pk'])

        serializer.save(restaurant=restaurant)


class SpecialHoursDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated,IsRestaurantOwner]
    lookup_field = 'id'  
    lookup_url_kwarg = 'special_hours_id'

    def get_queryset(self):

        return SpecialHours.objects.filter(
            restaurant_id=self.kwargs['pk']
        )


class RestaurantIsOpenView(generics.GenericAPIView):

    serializer_class = RestaurantAvailabilitySerializer

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


class RestaurantNextOpeningView(generics.GenericAPIView):

    serializer_class = RestaurantAvailabilitySerializer

    def get(self, request, *args, **kwargs):

        restaurant_id = self.kwargs['pk']

        next_opening = RestaurantAvailabilityService.get_next_opening_time(restaurant_id)

        data = {
            'restaurant_id': restaurant_id,
            'next_opening_time': next_opening,
        }

        serializer = self.get_serializer(data)

        return Response(serializer.data)
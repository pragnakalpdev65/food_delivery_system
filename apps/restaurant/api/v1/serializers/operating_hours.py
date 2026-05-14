from rest_framework import serializers

from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.operating_hours import (
    OperatingHours,
    SpecialHours
)

class OperatingHoursSerializer(serializers.ModelSerializer):
    day_of_week = serializers.IntegerField(min_value=1, max_value=7,read_only=True)
    class Meta:
        model = OperatingHours
        fields = [
            'id',
            'restaurant',
            'day_of_week',
            'opening_time',
            'closing_time',
            'is_closed',
        ]
        read_only_fields = ['restaurant']

    def validate(self, attrs):
        
        restaurant = self.context['view'].kwargs['pk']
        day = attrs.get('day_of_week')

        is_closed = attrs.get('is_closed', False)

        opening_time = attrs.get('opening_time')
        closing_time = attrs.get('closing_time')
        


        if OperatingHours.objects.filter(
            restaurant_id=restaurant,
            day_of_week=day
        ).exists():
            raise serializers.ValidationError(
                "Operating hours for this day already exist."
            )


        if not is_closed:

            if not opening_time:
                raise serializers.ValidationError({
                    'opening_time': (
                        'Opening time is required.'
                    )
                })

            if not closing_time:
                raise serializers.ValidationError({
                    'closing_time': (
                        'Closing time is required.'
                    )
                })

            if opening_time >= closing_time:
                raise serializers.ValidationError({
                    'closing_time': (
                        'Closing time must be after '
                        'opening time.'
                    )
                })

        return attrs


class SpecialHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpecialHours
        fields = [
            'id',
            'restaurant',
            'date',
            'opening_time',
            'closing_time',
            'is_closed',
            'reason',
        ]
        read_only_fields = ['restaurant']

    def validate(self, attrs):

        is_closed = attrs.get('is_closed', False)

        opening_time = attrs.get('opening_time')
        closing_time = attrs.get('closing_time')

        if not is_closed:

            if not opening_time:
                raise serializers.ValidationError({
                    'opening_time': (
                        'Opening time is required.'
                    )
                })

            if not closing_time:
                raise serializers.ValidationError({
                    'closing_time': (
                        'Closing time is required.'
                    )
                })

            if opening_time >= closing_time:
                raise serializers.ValidationError({
                    'closing_time': (
                        'Closing time must be after '
                        'opening time.'
                    )
                })

        return attrs


class RestaurantAvailabilitySerializer(serializers.Serializer):

    restaurant_id = serializers.UUIDField(read_only=True)

    is_open = serializers.BooleanField(read_only=True)

    next_opening_time = serializers.DateTimeField(read_only=True)
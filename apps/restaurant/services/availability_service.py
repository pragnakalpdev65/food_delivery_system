from datetime import datetime, timedelta

from django.utils import timezone

from apps.restaurant.models.operating_hours import (
    OperatingHours,
    SpecialHours
)
from apps.restaurant.models.restaurant import Restaurant


class RestaurantAvailabilityService:

    @staticmethod
    def get_todays_hours(restaurant_id):
        today = timezone.localdate()

        special_hours = SpecialHours.objects.filter(
            restaurant_id=restaurant_id,
            date=today
        ).first()

        if special_hours:
            return special_hours

        weekday = today.weekday()

        return OperatingHours.objects.filter(
            restaurant_id=restaurant_id,
            day_of_week=weekday
        ).first()

    @staticmethod
    def is_currently_open(restaurant_id):
        hours = RestaurantAvailabilityService.get_todays_hours(restaurant_id)
        if not hours:
            return False

        if hours.is_closed:
            return False

        now = timezone.localtime().time()
        if hours.opening_time <= hours.closing_time:
            return hours.opening_time <= now <= hours.closing_time
        else:
            return now >= hours.opening_time or now <= hours.closing_time

    @staticmethod
    def get_next_opening_time(restaurant_id):
        today = timezone.localdate()
        now = timezone.localtime()
        current_tz = timezone.get_current_timezone()

        for i in range(7):
            check_date = today + timedelta(days=i)

            special_hours = SpecialHours.objects.filter(
                restaurant_id=restaurant_id,
                date=check_date
            ).first()

            if special_hours:
                if special_hours.is_closed:
                    continue

                opening_datetime = timezone.make_aware(
                    datetime.combine(check_date, special_hours.opening_time),
                    current_tz
                )

                if opening_datetime > now:
                    return opening_datetime

            weekday = check_date.weekday()

            operating_hours = (
                OperatingHours.objects
                .filter(
                    restaurant_id=restaurant_id,
                    day_of_week=weekday,
                    is_closed=False
                )
                .first()
            )

            if operating_hours:
                opening_datetime = datetime.combine(
                    check_date,
                    operating_hours.opening_time,
                    tzinfo=current_tz
                )

                if opening_datetime > now:
                    return opening_datetime

        return None
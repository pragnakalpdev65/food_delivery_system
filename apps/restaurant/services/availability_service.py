from datetime import datetime, timedelta
import uuid
from django.utils import timezone
from apps.restaurant.models.operating_hours import (
    OperatingHours,
    SpecialHours,
)
from apps.restaurant.models.restaurant import Restaurant
class RestaurantAvailabilityService:

    @staticmethod
    def get_todays_hours(restaurant_id):
        """Fetches operational hours using a clean ID string or UUID."""
        today = timezone.localdate()

        special_hours = SpecialHours.objects.filter(
            restaurant_id=restaurant_id,
            date=today,
        ).first()

        if special_hours:
            return special_hours

        weekday = today.weekday()

        return OperatingHours.objects.filter(
            restaurant_id=restaurant_id,
            day_of_week=weekday,
        ).first()

    @staticmethod
    def is_currently_open(restaurant_or_id):
        """
        Determines if a restaurant is currently open.
        Accepts either a Restaurant model instance or a restaurant UUID/ID string.
        """
        # Type-safety check: extract id and model safely
        if isinstance(restaurant_or_id, (str, uuid.UUID)):
            restaurant_id = restaurant_or_id
            # Fetch instance from DB for fallback timings if needed
            restaurant = Restaurant.objects.filter(id=restaurant_id).first()
        else:
            restaurant_id = restaurant_or_id.id
            restaurant = restaurant_or_id

        if not restaurant:
            return False

        now = timezone.localtime().time()
        today_hours = RestaurantAvailabilityService.get_todays_hours(restaurant_id)

        if today_hours:
            if today_hours.is_closed:
                return False

            opening_time = today_hours.opening_time
            closing_time = today_hours.closing_time
        else:
            # Fallback to base Restaurant model timings
            opening_time = restaurant.opening_time
            closing_time = restaurant.closing_time

        # Safeguard against missing configurations
        if not opening_time or not closing_time:
            return False

        # Normal day timings (e.g., 09:00 - 22:00)
        if opening_time < closing_time:
            return opening_time <= now < closing_time

        # Overnight timings (e.g., 20:00 - 02:00)
        return now >= opening_time or now < closing_time

    @staticmethod
    def get_next_opening_time(restaurant_id):
        today = timezone.localdate()
        now = timezone.localtime()
        current_tz = timezone.get_current_timezone()

        for i in range(7):
            check_date = today + timedelta(days=i)

            special_hours = SpecialHours.objects.filter(
                restaurant_id=restaurant_id,
                date=check_date,
            ).first()

            if special_hours:
                if special_hours.is_closed:
                    continue

                opening_datetime = timezone.make_aware(
                    datetime.combine(
                        check_date,
                        special_hours.opening_time,
                    ),
                    current_tz,
                )

                if opening_datetime > now:
                    return opening_datetime

            weekday = check_date.weekday()

            operating_hours = OperatingHours.objects.filter(
                restaurant_id=restaurant_id,
                day_of_week=weekday,
                is_closed=False,
            ).first()

            if operating_hours:
                opening_datetime = timezone.make_aware(
                    datetime.combine(
                        check_date,
                        operating_hours.opening_time,
                    ),
                    current_tz,
                )

                if opening_datetime > now:
                    return opening_datetime

        return None
                                                                                                                       
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
        now_dt = timezone.localtime()
        now_time = now_dt.time()
        today = now_dt.date()
        yesterday = today - timedelta(days=1)

        today_hours = RestaurantAvailabilityService.get_todays_hours(restaurant_id)

        if today_hours and not today_hours.is_closed:
            if today_hours.opening_time < today_hours.closing_time:
                if today_hours.opening_time <= now_time < today_hours.closing_time:
                    return True
            else:
                if now_time >= today_hours.opening_time:
                    return True

        yesterday_hours = (
            SpecialHours.objects.filter(restaurant_id=restaurant_id, date=yesterday).first()
            or OperatingHours.objects.filter(
                restaurant_id=restaurant_id,
                day_of_week=yesterday.weekday()
            ).first()
        )

        if yesterday_hours and not yesterday_hours.is_closed:
            if yesterday_hours.opening_time > yesterday_hours.closing_time:
                if now_time < yesterday_hours.closing_time:
                    return True

        return False
    
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
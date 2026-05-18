from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from apps.order.models.order import Order, OrderRating
from apps.core.constants.choices import OrderStatus
from apps.users.models.profile import DriverProfile
from apps.core.constants.messages import AuthMessages
from apps.order.services.notification_service import NotificationService
class OrderRatingSerializer(serializers.ModelSerializer):

    overall_rating = serializers.ReadOnlyField()

    class Meta:
        model = OrderRating
        fields = [
            "id",
            "order",
            "food_quality",
            "delivery_speed",
            "packaging_quality",
            "overall_rating",
            "comment",
            "would_recommend",
            "had_issues",
            "issue_description",
            "created_at",
        ]

        read_only_fields = ["id","overall_rating","created_at"]

    def validate(self, attrs):

        request = self.context["request"]
        order = attrs.get("order")

        if self.instance is None:

            if order.customer != request.user:
                raise serializers.ValidationError(
                    AuthMessages.RATE_OWN_ORDER
                )

            if order.status.lower() != OrderStatus.DELIVERED:
                raise serializers.ValidationError(
                    AuthMessages.RATE_DELIVERED_ORDER
                )

            if not order.actual_delivery_time:
                raise serializers.ValidationError(
                    AuthMessages.ACTUAL_DELIVERY_TIME_NOT_FOUND
                )

            allowed_time = (
                order.actual_delivery_time + timedelta(days=7)
            )

            if timezone.now() > allowed_time:
                raise serializers.ValidationError(
                    AuthMessages.RATING_PERIOD_REQUIRED
                )

            if hasattr(order, "rating"):
                raise serializers.ValidationError(
                    AuthMessages.ALREADY_RATED
                )

        if self.instance:
            editable_until = (
                self.instance.created_at + timedelta(hours=24)
            )
            if timezone.now() > editable_until:
                raise serializers.ValidationError(
                    AuthMessages.RATING_IN_24_HOURS
                )

        if attrs.get("had_issues") and not attrs.get(
            "issue_description"
        ):
            raise serializers.ValidationError(
                {
                    "issue_description":
                    AuthMessages.ISSUE_DESCRIPTION_REQUIRED
                }
            )

        return attrs

    def create(self, validated_data):
        ratings = [
            validated_data["food_quality"],
            validated_data["delivery_speed"],
            validated_data["packaging_quality"],
        ]
        
        for rating in ratings:
            if rating < 1 or rating > 5:
                raise serializers.ValidationError(
                    AuthMessages.RATING_VALIDATION
                )

        validated_data["overall_rating"] = round(
            sum(ratings) / len(ratings)
        )

        validated_data["customer"] = (
            self.context["request"].user
        )

        rating = super().create(validated_data)

        restaurant = rating.order.restaurant

        if hasattr(restaurant, "update_average_rating"):
            restaurant.update_average_rating()

        driver = rating.order.driver

        if driver and hasattr(driver, "update_average_rating"):
            driver.update_average_rating()

        return rating

    def update(self, instance, validated_data):

        ratings = [
            validated_data.get(
                "food_quality",
                instance.food_quality
            ),
            validated_data.get(
                "delivery_speed",
                instance.delivery_speed
            ),
            validated_data.get(
                "packaging_quality",
                instance.packaging_quality
            ),
        ]

        validated_data["overall_rating"] = round(
            sum(ratings) / len(ratings)
        )

        rating = super().update(instance, validated_data)

        restaurant = rating.order.restaurant

        if hasattr(restaurant, "update_average_rating"):
            restaurant.update_average_rating()

        driver = rating.order.driver

        if driver and hasattr(driver, "update_average_rating"):
            driver.update_average_rating()

        return rating
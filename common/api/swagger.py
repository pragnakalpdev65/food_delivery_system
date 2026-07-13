"""Shared OpenAPI / Swagger serializers for consistent schema docs."""

from rest_framework import serializers

from apps.core.constants.choices import OrderStatus


class MessageResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(required=False)
    message = serializers.CharField(required=False)


class FavoriteCheckResponseSerializer(serializers.Serializer):
    is_favorited = serializers.BooleanField()


class FavoriteCreateRequestSerializer(serializers.Serializer):
    restaurant_id = serializers.UUIDField(required=False)
    item_id = serializers.UUIDField(required=False)


class AssignDriverRequestSerializer(serializers.Serializer):
    driver_id = serializers.UUIDField()


class AssignDriverResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class UpdateOrderStatusRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)


class UpdateOrderStatusResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    status = serializers.ChoiceField(choices=OrderStatus.choices)


class OrderETAResponseSerializer(serializers.Serializer):
    estimated_delivery_time = serializers.DateTimeField()


class ErrorResponseSerializer(serializers.Serializer):
    status = serializers.CharField(default="error")
    code = serializers.CharField()
    message = serializers.CharField()

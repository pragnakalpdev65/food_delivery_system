from rest_framework import serializers
from apps.order.models.cancellation import CancellationPolicy


class CancellationPolicySerializer(serializers.ModelSerializer):

    class Meta:
        model = CancellationPolicy
        fields = ["full_refund_window","partial_refund_window","partial_refund_percentage","allow_customer_cancellation",]

    def validate(self, data):
        full = data.get("full_refund_window")
        partial = data.get("partial_refund_window")

        if full is not None and partial is not None:
            if full >= partial:
                raise serializers.ValidationError(
                    "Partial refund window must be greater than full refund window"
                )

        percentage = data.get("partial_refund_percentage")
        if percentage is not None and not (0 <= percentage <= 100):
            raise serializers.ValidationError(
                "Refund percentage must be between 0 and 100"
            )

        return data
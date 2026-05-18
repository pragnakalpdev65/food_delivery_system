from django.utils import timezone
from decimal import Decimal
from apps.core.constants.choices import OrderStatus
from apps.core.constants.messages import AuthMessages
class CancellationServices:
    
    @staticmethod
    def calculate_refund(order):
        policy = getattr(order.restaurant,"cancellation_policy",None)
        
        if not policy:
            full_window = 5
            partial_window = 15
            refund_percentage = 50
        else:
            full_window = policy.full_refund_window
            partial_window = policy.partial_refund_window
            refund_percentage = policy.partial_refund_percentage


        now = timezone.now()
        elapsed_minutes = (now - order.created_at).total_seconds() / 60
        total = order.total_amount

        if elapsed_minutes <= full_window:
            return total, 100

        if elapsed_minutes <= partial_window:
            refund_amount = ((total * Decimal(refund_percentage)) / Decimal(100)).quantize(Decimal('0.01'))
            return refund_amount, refund_percentage

        return Decimal("0.00"), 0
    
    
    @staticmethod
    def can_cancel(order, user):

        if hasattr(order, "cancellation"):
            return False, AuthMessages.ALREADY_CANCELLED

        if order.status in [OrderStatus.PREPARING,OrderStatus.DELIVERED,OrderStatus.CANCELLED]:
            return False, AuthMessages.CAN_NOT_BE_CANCELLED

        policy = getattr(order.restaurant, "cancellation_policy", None)

        if policy and not policy.allow_customer_cancellation:
            return False, AuthMessages.CANCELLATION_NOT_ALLOWED

        if order.customer != user:
            return False,"Not allowed"

        return True,None
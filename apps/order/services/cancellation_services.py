from django.utils import timezone
from decimal import Decimal
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
            refund_amount = (total * Decimal(refund_percentage)) / Decimal(100)
            return refund_amount, refund_percentage

        return Decimal("0.00"), 0
    
    
    @staticmethod
    def can_cancel(order, user):

        if hasattr(order, "cancellation"):
            return False, "Order already cancelled"

        if order.status in ["delivered", "cancelled"]:
            return False,"Order cannot be cancelled"

        policy = getattr(order.restaurant, "cancellation_policy", None)

        if policy and not policy.allow_customer_cancellation:
            return False,"Restaurant does not allow cancellations"

        if order.customer != user:
            return False,"Not allowed"

        return True,None
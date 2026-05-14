from django.db import models
from common.models.base import UUIDModel,TimestampedModel
from apps.restaurant.models.restaurant import Restaurant
from apps.order.models.order import Order
from apps.users.models.user import CustomUser
from apps.core.constants.choices import Reasons

class CancellationPolicy(UUIDModel,TimestampedModel):
    restaurant = models.OneToOneField(Restaurant,on_delete=models.CASCADE,related_name='cancellation_policy')
    full_refund_window = models.IntegerField(default=5)
    partial_refund_window = models.IntegerField(default=15)
    partial_refund_percentage = models.IntegerField(default=50)
    allow_customer_cancellation = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.restaurant.name} Cancellation Policy"
    
class OrderCancellation(UUIDModel,TimestampedModel):
    REFUND_PERCENTAGE_CHOICES = (
        (0, '0%'),
        (50, '50%'),
        (100, '100%'),
    )
    order = models.OneToOneField(Order,on_delete=models.CASCADE,related_name='cancellation')
    cancelled_by = models.ForeignKey(CustomUser,on_delete=models.SET_NULL,null=True,blank=True)
    reason = models.CharField(max_length=30,choices=Reasons.choices,default=Reasons.OTHER,db_index=True)
    reason_detail = models.TextField(blank=True,null=True)
    refund_amount = models.DecimalField(max_digits=8,decimal_places=2,default=0.00)
    refund_percentage = models.IntegerField(choices=REFUND_PERCENTAGE_CHOICES,default=0)
    cancelled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cancellation - Order #{self.order.order_number}"
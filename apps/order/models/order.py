from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.users.models.user import CustomUser
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.core.constants.status import OrderStatus

class Order(TimestampedModel,UUIDModel):
    
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="orders")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name="orders")
    driver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name="driver_orders", null=True)
    order_number = models.PositiveIntegerField(unique=True, auto_created=True, null=True)
    status = models.CharField(max_length=20,choices=OrderStatus.choices,default=OrderStatus.PENDING,db_index=True)    
    delivery_address = models.TextField()
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    special_instructions = models.TextField(null=True, blank=True) 
    estimated_delivery_time = models.DateTimeField(null=True)
    actual_delivery_time = models.DateTimeField(null=True)

    def can_cancel(self):
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def is_delivered(self):
        return self.status == OrderStatus.DELIVERED

    def items_count(self):
        return self.items.count()

    def total_items_quantity(self):
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0
 
    def calculate_total(self):
        self.total_amount = self.subtotal + self.delivery_fee + self.tax
        return self.total_amount
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            last_order = (
                Order.objects
                .exclude(order_number__isnull=True)
                .order_by('-order_number')
                .first()
            )
            if last_order and last_order.order_number:
                self.order_number = last_order.order_number + 1
            else:
                self.order_number = 1
        super().save(*args, **kwargs)
class OrderItem(TimestampedModel,UUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00,  help_text="Snapshot of item price at order time")
    special_instructions = models.TextField(null=True, blank=True) 

    def get_total(self):
        return self.quantity * self.price
class Review(TimestampedModel,UUIDModel):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="reviews")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name="reviews")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="reviews")
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="reviews")
    comment = models.TextField(null=True, blank=True)
    rating =models.IntegerField()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        if self.restaurant:
            self.restaurant.update_average_rating()
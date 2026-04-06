from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.users.models.user import CustomUser
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem

class Order(TimestampedModel,UUIDModel):
    
    STATUS_TYPES=(
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('preparing','Preparing'),
        ('ready','Ready'),
        ('picked_up','Picked Up'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled'),
    )
    
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="orders")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name="orders")
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="driver_orders", null=True)
    order_number = models.PositiveIntegerField(unique=True, auto_created=True)
    status = models.CharField(max_length=20, choices=STATUS_TYPES, default="pending", db_index=True)
    delivery_address = models.TextField()
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    special_instructions = models.TextField(null=True, blank=True) 
    estimated_delivery_time = models.DateTimeField(null=True)
    actual_delivery_time = models.DateTimeField(null=True)

    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(TimestampedModel,UUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00,  help_text="Snapshot of item price at order time")
    special_instructions = models.TextField(null=True, blank=True) 

class Review(TimestampedModel,UUIDModel):
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="reviews")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,related_name="reviews")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="reviews")
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name="reviews")
    comment = models.TextField(null=True, blank=True)
    rating =models.IntegerField()

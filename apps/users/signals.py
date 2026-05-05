import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomerProfile, DriverProfile
from apps.order.models.order import Order, Review, OrderItem

User=get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender = User)
@transaction.atomic()
def create_profile(sender,instance, created, **kwargs):
    if created:
        if instance.user_type == "customer":
            CustomerProfile.objects.create(user=instance)

        if instance.user_type == "delivery_driver":
            DriverProfile.objects.create(user=instance)         

@receiver(post_save, sender=Order)
def notify_restaurant(sender, instance, created, **kwargs):
    if created:
        print(f"New order received for {instance.restaurant.name}")
        
@receiver(post_save, sender=Order)
def update_stats(sender, instance, **kwargs):
    if instance.status == "Delivered":
        customer = instance.customer
        driver = instance.driver

        customer.total_orders += 1
        customer.save()

        if driver:
            driver.completed_deliveries += 1
            driver.save()
            
@receiver(post_save, sender=Review)
def update_rating(sender, instance, created, **kwargs):
    if created:
        restaurant = instance.restaurant
        reviews = restaurant.reviews.all()
        avg = sum(r.rating for r in reviews) / reviews.count()
        restaurant.average_rating = avg
        restaurant.save()
        
@receiver(post_save, sender=OrderItem)
def update_subtotal(sender, instance, **kwargs):
    order = instance.order
    order.subtotal = sum(item.total_price for item in order.items.all())
    order.save()


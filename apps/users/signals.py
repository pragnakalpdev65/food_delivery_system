import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import CustomerProfile, DriverProfile, RestaurantOwnerProfile
from apps.order.models.order import Order, Review, OrderItem
from apps.core.constants.choices import UserType, OrderStatus

User=get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender = User)
@transaction.atomic()
def create_profile(sender,instance, created, **kwargs):
    if created:
        if instance.user_type == UserType.CUSTOMER:
            CustomerProfile.objects.create(user=instance)

        if instance.user_type == UserType.DELIVERY_DRIVER:
            DriverProfile.objects.create(user=instance)

        if instance.user_type == UserType.RESTAURANT_OWNER:
            RestaurantOwnerProfile.objects.create(user=instance)

@receiver(post_save, sender=Order)
def notify_restaurant(sender, instance, created, **kwargs):
    if created:
        logger.info(f"New order received for {instance.restaurant.name}")


@receiver(pre_save, sender=Order)
def cache_previous_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = sender.objects.values_list("status", flat=True).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def update_stats(sender, instance, created, **kwargs):
    previous_status = getattr(instance, "_previous_status", None)
    if instance.status == OrderStatus.DELIVERED and previous_status != OrderStatus.DELIVERED:
        customer = instance.customer
        driver = instance.driver

        if hasattr(customer, "customer_profile"):
            profile = customer.customer_profile
            profile.total_orders += 1
            profile.save(update_fields=["total_orders"])

        if driver and hasattr(driver, "driver_profile"):
            profile = driver.driver_profile
            profile.total_deliveries += 1
            profile.save(update_fields=["total_deliveries"])


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
    subtotal = sum(item.get_total() for item in order.items.all())
    if order.subtotal != subtotal:
        Order.objects.filter(pk=order.pk).update(subtotal=subtotal)


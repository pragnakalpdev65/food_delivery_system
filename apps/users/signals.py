import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomerProfile, DriverProfile
User=get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender = User)
@transaction.atomic()
def create_profile(sender,instance, created, **kwargs):
    if created:
        if instance.user_type == "customer":
            CustomerProfile.objects.create(user=instance)
        if instance.user_type == "restaurant_owner": 
            CustomerProfile.objects.create(user=instance)  
        if instance.user_type == "delivery_driver":
            DriverProfile.objects.create(user=instance)         

        
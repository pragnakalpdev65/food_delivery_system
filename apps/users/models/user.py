from django.db import models
from django.contrib.auth.models import AbstractUser
from common.models.base import TimestampedModel, UUIDModel
# Create your models here.

class CustomUser(AbstractUser, TimestampedModel, UUIDModel):
    
    TYPE_OF_USER = (
        ("customer","Customer"),
        ("restaurant_owner","Restaurant Owner"),
        ("delivery_driver","Delivery Driver"),
    )
    username = models.CharField(max_length = 150, unique = True, help_text="Username for login")
    email = models.EmailField(max_length=255, unique=True, help_text="Email address for login and notifications")  
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True, help_text="Contact number for notifications")
    first_name = models.CharField( max_length=255, blank=True, help_text="User's full display name")
    last_name = models.CharField( max_length=255, blank=True, help_text="User's full display name")
    user_type = models.CharField( max_length=50, choices=TYPE_OF_USER, default="customer", db_index=True, help_text= "Type of user")
    is_active = models.BooleanField(default=True, help_text="Is this user account active?")
    is_verified = models.BooleanField(default=False, help_text="Has the user verified their email?")
    
    
    def __str__(self):
        return self.username
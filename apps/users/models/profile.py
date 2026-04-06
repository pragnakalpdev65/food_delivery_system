from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.users.models.user import CustomUser

from django.core.exceptions import ValidationError

def validate_avatar(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Avatar must be less than 5MB")
    

class CustomerProfile(TimestampedModel,UUIDModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="customer_profile")
    avatar = models.ImageField(upload_to="avatars/",validators=[validate_avatar], blank=True, null=True)
    default_address =  models.TextField(max_length=500, null=True, blank=True)
    total_orders = models.PositiveIntegerField(default = 0)
    loyalty_points = models.PositiveIntegerField(default = 0)
    
    def __str__(self):
        return self.user
    
   
class Address(TimestampedModel,UUIDModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="addresses") 
    pin_code = models.CharField(max_length=10)
    label= models.CharField(max_length=50)
    address = models.TextField()
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.label} - {self.address}"
       
class DriverProfile(TimestampedModel,UUIDModel):
    TYPE_OF_VEHICLE = (
        ("bike","Bike"),
        ("scooter","Scooter"),
        ("car","Car"),
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="driver_profile")
    avatar = models.ImageField(upload_to="avatars/",validators=[validate_avatar], blank=True, null=True)
    vehicle_type = models.CharField( max_length=20, choices=TYPE_OF_VEHICLE, default="bike", db_index=True, help_text= "Type of Vehicle")
    vehicle_number = models.CharField(max_length=20)
    license_number = models.CharField(max_length=20)
    is_available = models.BooleanField(default=True)
    total_deliveries = models.PositiveIntegerField(default=0)
    average_rating =models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    def __str__(self):
        return self.user
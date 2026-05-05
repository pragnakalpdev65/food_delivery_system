from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.users.models.user import CustomUser

from django.core.exceptions import ValidationError
from apps.core.constants.messages import AuthMessages
from django.db.models import Count

def validate_avatar(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError(AuthMessages.AVATAR_VALIDATION)    
class CustomerProfile(TimestampedModel,UUIDModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="customer_profile")
    avatar = models.ImageField(upload_to="avatars/",validators=[validate_avatar], blank=True, null=True)
    default_address = models.ForeignKey("Address", on_delete=models.SET_NULL, null=True, blank=True, related_name="default_for")
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
    

    def update_availability(self, status: bool):
        self.is_available = status
        self.save(update_fields=['is_available'])

    def get_delivery_stats(self):
        return {
            "total_deliveries": self.orders.filter(status="DELIVERED").count(),
            "active_deliveries": self.orders.filter(status__in=["ASSIGNED", "PICKED"]).count(),
        }
from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.users.models.user import CustomUser
from django.core.exceptions import ValidationError

def validate_logo(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Logo must be less than 5MB")

def validate_banner(image):
    if image.size > 10 * 1024 * 1024:
        raise ValidationError("Banner must be less than 10MB")
    
class Restaurant(TimestampedModel,UUIDModel):
    
    TYPE_OF_CUISINE =(
        ('italian','Italian'),
        ('chinese','Chinese'),
        ('indian','Indian'),
        ('mexican','Mexican'),
        ('american','American'),
        ('japanese','Japanese'),
        ('thai','Thai'),
        ('mediterranean','Mediterranean')     
    )
    
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="restaurants")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cuisine_type = models.CharField(max_length=30, choices=TYPE_OF_CUISINE, default="indian", db_index=True, help_text= "Type of Cuisine")
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)  
    logo = models.ImageField(upload_to="restaurants/logo/", validators=[validate_logo], blank=True, null=True) 
    banner = models.ImageField(upload_to="restaurants/banner/", validators=[validate_banner], blank=True, null=True) 
    opening_time = models.TimeField() 
    closing_time = models.TimeField() 
    is_open = models.BooleanField(default=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    minimum_order = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    average_rating =models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.name
from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.restaurant.models.restaurant import Restaurant
from django.core.exceptions import ValidationError

def validate_image(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Image must be less than 5MB")

class MenuItem(TimestampedModel,UUIDModel):
    
    CATEGORIES = (
        ('appetizer','Appetizer'),
        ('main_course','Main Course'),
        ('dessert', 'Dessert'),
        ('Beverage','beverage'),
        ('side_dish','Side Dish'),
    )
    
    DIETARIES = (
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten Free'),
        ('dairy_free', 'Dairy Free'),
        ('none', 'None'),
    )
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="appetizer", db_index=True)
    dietary_info = models.CharField(max_length=20, choices=DIETARIES, default="none")
    image = models.ImageField(upload_to="menu_items/image/",validators=[validate_image], blank=True, null=True)
    is_available = models.BooleanField(default=True, db_index=True)
    preparation_time = models.DurationField(help_text="Preparation time")    
    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"
    
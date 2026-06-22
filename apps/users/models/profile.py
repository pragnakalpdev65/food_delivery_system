from django.db import models
from common.models.base import TimestampedModel, UUIDModel
from apps.users.models.user import CustomUser

from django.core.exceptions import ValidationError
from apps.core.constants.messages import AuthMessages
from django.db.models import Avg, Sum, Count
from apps.order.models.order import Order
from apps.core.constants.choices import OrderStatus

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
        return f"Profile of {self.user.username}"    
class Address(TimestampedModel,UUIDModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="addresses") 
    pin_code = models.CharField(max_length=10)
    label= models.CharField(max_length=50)
    address = models.TextField()
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} - {self.address}"     
        
class RestaurantOwnerProfile(TimestampedModel, UUIDModel):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="restaurant_owner_profile"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        validators=[validate_avatar],
        blank=True,
        null=True
    )

    business_name = models.CharField(max_length=255, blank=True)
    contact_number = models.CharField(max_length=20, blank=True)

    total_restaurants = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)

    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00
    )

    def __str__(self):
        return f"Restaurant Owner Profile - {self.user.username}"

    def update_statistics(self):
        restaurants = self.user.restaurants.all()

        self.total_restaurants = restaurants.count()

        self.average_rating = (
            restaurants.aggregate(
                avg=Avg("average_rating")
            )["avg"]
            or 0
        )

        orders = Order.objects.filter(
            restaurant__owner=self.user,
            status=OrderStatus.DELIVERED
        )

        self.total_orders = orders.count()

        self.total_revenue = (
            orders.aggregate(
                revenue=Sum("total_amount")
            )["revenue"]
            or 0
        )

        self.save(
            update_fields=[
                "total_restaurants",
                "total_orders",
                "total_revenue",
                "average_rating",
            ]
        ) 
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
        
    def update_average_rating(self):
        avg = (
            self.user.driver_orders
            .filter(rating__isnull=False)
            .aggregate(avg=Avg("rating__overall_rating"))["avg"]
        )

        self.average_rating = round(avg or 0, 2)
        self.save(update_fields=["average_rating"])
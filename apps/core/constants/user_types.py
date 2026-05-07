from django.db import models


class UserType(models.TextChoices):
    """
    Canonical user type constants.
    
    These are the authoritative values for user_type field in CustomUser model.
    All permission checks and comparisons must use these constants to ensure
    consistency and prevent authorization bypasses due to string variations.
    """
    CUSTOMER = "customer", "Customer"
    RESTAURANT_OWNER = "restaurant_owner", "Restaurant Owner"
    DELIVERY_DRIVER = "delivery_driver", "Delivery Driver"

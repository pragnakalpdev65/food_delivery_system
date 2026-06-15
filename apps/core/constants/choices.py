from django.db import models
from django.utils.translation import gettext_lazy as _
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

class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    PREPARING = "preparing", "Preparing"
    READY = "ready", "Ready"
    PICKED_UP = "picked_up", "Picked Up"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"
    
class WeekDays(models.IntegerChoices):
    MONDAY = 0, _("Monday")
    TUESDAY = 1, _("Tuesday")
    WEDNESDAY = 2, _("Wednesday")
    THURSDAY = 3, _("Thursday")
    FRIDAY = 4, _("Friday")
    SATURDAY = 5, _("Saturday")
    SUNDAY = 6, _("Sunday")

class Reasons(models.TextChoices):
    CUSTOMER_REQUEST = "customer_request","Customer Request"
    RESTAURANT_UNAVAILABLE = "restaurant_unavailable","Restaurant_Unavailable"
    ITEM_UNAVAILABLE = "item_unavailable","Item_Unavailable"
    DELIVERY_ISSUE = "delivery_issue", "Delivery_Issue"
    PAYMENT_FAILED = "payment_failed", "Payment_Failed"
    OTHER = "other", "Other"  
    
class InstructionCategory(models.TextChoices):
    DELIVERY = "delivery", "Delivery"
    FOOD = "food","Food"
    PACKAGING = "packaging", "Packaging"
    
class ContactPreference(models.TextChoices):
    CALL= "call","Call"
    TEXT = "text","Text"
    DO_NOT_DISTURB = "do_not_disturb", "Do Not Disturb"
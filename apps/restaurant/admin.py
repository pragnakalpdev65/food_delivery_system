from django.contrib import admin
from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.models.operating_hours import OperatingHours,SpecialHours
# Register your models here.

admin.site.register([Restaurant, MenuItem, OperatingHours,SpecialHours])
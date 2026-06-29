from django.contrib import admin
from apps.users.models.user import CustomUser 
from apps.users.models.profile import CustomerProfile,DriverProfile,Address,RestaurantOwnerProfile
from apps.users.models.favorites import FavoriteMenuItem, FavoriteRestaurant
# Register your models here.

admin.site.register([CustomUser,CustomerProfile,DriverProfile,RestaurantOwnerProfile,Address,FavoriteMenuItem,FavoriteRestaurant])
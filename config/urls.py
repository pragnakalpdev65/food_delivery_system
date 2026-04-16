"""
URL configuration for food_delivery_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path("api/v1/users/", include("apps.users.api.v1.urls")),

    # Restaurant and order API endpoints are not implemented yet.
    # Remove these includes or add URL patterns in the respective app modules before enabling them.
    # path("api/v1/restaurant/", include("apps.restaurant.api.v1.urls")),
    # path("api/v1/order/", include("apps.order.api.v1.urls")),
]

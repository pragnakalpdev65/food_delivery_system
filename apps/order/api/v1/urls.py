from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.orders import OrderViewSet
from .views.order_management import OrderManagementViewSet
from .views.review import ReviewView

router = DefaultRouter(trailing_slash=False)
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"ordermanagement", OrderManagementViewSet, basename="ordermanagement")
# router.register(r"menuitem", MenuItemViewSet, basename="menuitem")

urlpatterns = [
    path("", include(router.urls)),
    path("review",ReviewView.as_view(),name = "Review"),
    
]
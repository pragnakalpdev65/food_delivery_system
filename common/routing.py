from django.urls import re_path
from apps.order.consumers import (
    OrderConsumer,
    OrderManagementConsumer,
    RestaurantDashboardConsumer,
    CustomerConsumer,
    DriverConsumer,
)

websocket_urlpatterns = [
    re_path(r"ws/orders/(?P<order_id>\d+)/$", OrderConsumer.as_asgi()),
    re_path(r"ws/orders/management/(?P<restaurant_id>\d+)/$", OrderManagementConsumer.as_asgi()),
    re_path(r"ws/restaurants/(?P<restaurant_id>\d+)/$", RestaurantDashboardConsumer.as_asgi()),
    re_path(r"ws/customers/$", CustomerConsumer.as_asgi()),
    re_path(r"ws/drivers/$", DriverConsumer.as_asgi()),
]
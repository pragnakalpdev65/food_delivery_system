from django.urls import re_path
from apps.order.consumers import (
    OrderConsumer,
    OrderManagementConsumer,
    RestaurantDashboardConsumer,
)

websocket_urlpatterns = [
    re_path(r"ws/orders/(?P<order_id>[^/]+)/$", OrderConsumer.as_asgi()),
    re_path(r"ws/orders/management/(?P<order_id>[^/]+)/$", OrderManagementConsumer.as_asgi()),
    re_path(r"ws/restaurants/(?P<restaurant_id>[^/]+)/$", RestaurantDashboardConsumer.as_asgi()),
]
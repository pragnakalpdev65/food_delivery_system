from django.urls import re_path

from apps.order.consumers import (
    UUID_PATH,
    OrderConsumer,
    OrderManagementConsumer,
    RestaurantDashboardConsumer,
    CustomerConsumer,
    DriverConsumer,
)

websocket_urlpatterns = [
    # Restaurant Order Section (primary for restaurant owners)
    re_path(
        rf"ws/orders/management/(?P<restaurant_id>{UUID_PATH})/$",
        OrderManagementConsumer.as_asgi(),
    ),
    # Single order tracking
    re_path(
        rf"ws/orders/(?P<order_id>{UUID_PATH})/$",
        OrderConsumer.as_asgi(),
    ),
    # Restaurant dashboard (new orders)
    re_path(
        rf"ws/restaurants/(?P<restaurant_id>{UUID_PATH})/$",
        RestaurantDashboardConsumer.as_asgi(),
    ),
    re_path(r"ws/customers/$", CustomerConsumer.as_asgi()),
    re_path(r"ws/drivers/$", DriverConsumer.as_asgi()),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.orders import OrderViewSet
from .views.review import ReviewView

from apps.order.api.v1.views.rating import (
    CreateOrderRatingView,
    RetrieveOrderRatingView,
    UpdateOrderRatingView,
    MyRatingsView,
)
from apps.order.api.v1.views.cancellation import CancellationView,CancellationPolicyView
from apps.order.api.v1.views.instruction_templates import InstructionTemplateListView

router = DefaultRouter(trailing_slash=False)
router.register(r"orders", OrderViewSet, basename="orders")
# router.register(r"menuitem", MenuItemViewSet, basename="menuitem")

urlpatterns = [
    path("", include(router.urls)),
    path("review",ReviewView.as_view(),name = "Review"),
    path("<uuid:order_id>/rate/",CreateOrderRatingView.as_view(),name="create-order-rating",),
    path("<uuid:order_id>/rating/",RetrieveOrderRatingView.as_view(),name="get-order-rating",),
    path("<uuid:order_id>/rating/update/",UpdateOrderRatingView.as_view(),name="update-order-rating",),
    path("users/my-ratings/",MyRatingsView.as_view(),name="my-ratings",),
    path("instruction-templates/",InstructionTemplateListView.as_view(),name="instruction-templates"),
    path("<uuid:order_id>/cancel/",CancellationView.as_view(),name="order-cancel",),
    path("<uuid:order_id>/cancel/info",CancellationView.as_view(),name="cancellation-info",),
    path("<uuid:restaurant_id>/cancellation-policy/",CancellationPolicyView.as_view(),name="cancellation-policy",),
]
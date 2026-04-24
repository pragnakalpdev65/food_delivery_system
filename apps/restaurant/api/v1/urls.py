# # restaurant-list
# # restaurant
# # restaurant - details
# # resturant-menu

# from django.urls import path
# # from .views.restaurant import RestaurantView, RestaurantDetailsView, RestaurantMenuSerializer
# from .views.restaurant import RestaurantView

# urlpatterns = [
#         path("restaurants/", RestaurantView.as_view(), name="restaurants"),
#         # path("restaurants-list/", RestaurantView.as_view(), name="restaurants-list"),
#         # path("restaurants-details/", RestaurantDetailsView.as_view(), name="restaurants-details"),
#         # path("restaurants-menu/", RestaurantMenuSerializer.as_view(), name="restaurants-menu"),
# ]
  
  
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.restaurant import RestaurantViewSet, RestaurantMenuView
from .views.menu import MenuItemViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"restaurants", RestaurantViewSet, basename="restaurants")
router.register(r"menuitem", MenuItemViewSet, basename="menuitem")

urlpatterns = [
    path("", include(router.urls)),

    path(
        "restaurants/<int:restaurant_id>/menu/",
        RestaurantMenuView.as_view(),
        name="restaurant-menu",
    ),
]
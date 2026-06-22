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

from .views.restaurant import RestaurantViewSet, RestaurantMenuView, MyRestaurantsView,RestaurantOrderListView
from .views.menu import MenuItemViewSet

from apps.restaurant.api.v1.views.operating_hours import (
    OperatingHoursListCreateView,
    OperatingHoursUpdateView,
    SpecialHoursListCreateView,
    SpecialHoursDeleteView,
    RestaurantIsOpenView,
    RestaurantNextOpeningView
)

router = DefaultRouter(trailing_slash=False)
router.register(r"restaurants", RestaurantViewSet, basename="restaurants")
router.register(r"menuitem", MenuItemViewSet, basename="menuitem")

urlpatterns = [
    path("", include(router.urls)),
    
    path(
        "my-restaurants/",
        MyRestaurantsView.as_view(),
        name="my-restaurants",
    ),
    path(
        "restaurants/<uuid:restaurant_id>/menu/",
        RestaurantMenuView.as_view(),
        name="restaurant-menu",
    ),
    path(
    "my-orders/",
    RestaurantOrderListView.as_view(),
    name="restaurant-orders",
    ),
    
    path(
        '<uuid:pk>/operating-hours/',
        OperatingHoursListCreateView.as_view(),
        name='operating-hours'
    ),

    path(
        '<uuid:pk>/operating-hours/<int:day>/',
        OperatingHoursUpdateView.as_view(),
        name='operating-hours-update'
    ),

    path(
        '<uuid:pk>/special-hours/',
        SpecialHoursListCreateView.as_view(),
        name='special-hours'
    ),

    path(
       '<uuid:pk>/special-hours/<uuid:special_hours_id>/',
        SpecialHoursDeleteView.as_view(),
        name='special-hours-delete'
    ),

    path(
        '<uuid:pk>/is-open/',
        RestaurantIsOpenView.as_view(),
        name='restaurant-is-open'
    ),

    path(
        '<uuid:pk>/next-opening/',
        RestaurantNextOpeningView.as_view(),
        name='restaurant-next-opening'
    ),

]




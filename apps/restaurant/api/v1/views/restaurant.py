from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.restaurant.models.restaurant import Restaurant
from apps.restaurant.api.v1.serializers.restaurant import RestaurantSerializer,RestaurantDetailsSerializer
from apps.permissions.restaurant_permissions import IsOwnerOrReadOnly
from rest_framework.generics import ListAPIView
from apps.restaurant.models.menu import MenuItem
from apps.restaurant.api.v1.serializers.menu import MenuItemSerializer


class RestaurantViewSet(ModelViewSet):
    queryset = Restaurant.objects.all()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [IsAuthenticatedOrReadOnly()]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["cuisine_type", "is_open"]
    search_fields = ["name", "cuisine_type"]
    ordering_fields = ["rating", "delivery_fee"]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
       
    queryset = Restaurant.objects.all().order_by('id') 
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return RestaurantDetailsSerializer
        return RestaurantSerializer

class RestaurantMenuView(ListAPIView):
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        restaurant_id = self.kwargs.get("restaurant_id")
        return MenuItem.objects.filter(restaurant_id=restaurant_id)
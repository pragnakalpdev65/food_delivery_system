import django_filters
from django.db.models import Q

from apps.order.models.order import Order


class OrderFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    min_amount = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")

    restaurant = django_filters.UUIDFilter(field_name="restaurant_id")

    has_rating = django_filters.BooleanFilter(method="filter_has_rating")

    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Order
        fields = [
            "status",
            "restaurant",
        ]

    def filter_has_rating(self, queryset, name, value):
        if value:
            return queryset.filter(rating__isnull=False)

        return queryset.filter(rating__isnull=True)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(order_number__icontains=value)
            | Q(restaurant__name__icontains=value)
        )
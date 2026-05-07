from rest_framework.pagination import PageNumberPagination, CursorPagination, LimitOffsetPagination
class StandardPagination(PageNumberPagination): 
    page_size = 10

class RestaurantPagination(PageNumberPagination):
    page_size = 20


class MenuItemPagination(PageNumberPagination):
    page_size = 30


class OrderPagination(CursorPagination):
    page_size = 25


class ReviewPagination(LimitOffsetPagination):
    default_limit = 20
    max_limit = 50
from django.contrib import admin
from apps.order.models.order import Order,OrderItem,OrderRating
from apps.order.models.cancellation import OrderCancellation,CancellationPolicy
from apps.order.models.instruction_templates import InstructionTemplate
# Register your models here.

admin.site.register([Order, OrderItem, OrderRating,OrderCancellation,CancellationPolicy, InstructionTemplate])
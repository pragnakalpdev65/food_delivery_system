from rest_framework.permissions import IsAuthenticated
from apps.users.api.v1.serializers.order_stats import OrderStatsSerializer
from rest_framework.response import Response
from rest_framework import generics
from drf_spectacular.utils import extend_schema

@extend_schema(
    description="Get statistics for the authenticated user's orders",
    responses=OrderStatsSerializer,
)        
class UserOrderStatsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatsSerializer

    def get(self, request):
        serializer = self.get_serializer(
            instance={},
            context={"request": request}
        )
        return Response(serializer.data)
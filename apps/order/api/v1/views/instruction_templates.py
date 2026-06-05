from rest_framework.views import APIView
from rest_framework import generics, status
from apps.order.api.v1.serializers.instruction_templates import InstructionTemplateSerializer
from apps.order.models.instruction_templates import InstructionTemplate
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=["Orders"],
    description="List active instruction templates, optionally filtered by category",
    responses=InstructionTemplateSerializer(many=True),
)
class InstructionTemplateListView(generics.ListAPIView):
    serializer_class = InstructionTemplateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = InstructionTemplate.objects.filter(is_active=True)

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)

        return queryset.order_by('-usage_count')
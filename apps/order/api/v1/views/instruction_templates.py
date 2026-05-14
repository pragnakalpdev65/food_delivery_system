from rest_framework.views import APIView
from rest_framework import generics, status
from apps.order.api.v1.serializers.intsruction_templates import InstructionTemplateSerializer
from apps.order.models.instruction_templates import InstructionTemplate

class InstructionTemplateListView(generics.ListAPIView):
    serializer_class = InstructionTemplateSerializer
    pagination_class = None 

    def get_queryset(self):
        return InstructionTemplate.objects.filter(is_active=True)
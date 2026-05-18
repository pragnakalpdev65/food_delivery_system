from rest_framework import serializers
from apps.order.models.instruction_templates import InstructionTemplate

class InstructionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructionTemplate
        fields = ['id', 'category', 'text']
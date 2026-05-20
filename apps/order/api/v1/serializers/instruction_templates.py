from rest_framework import serializers
from apps.order.models.instruction_templates import InstructionTemplate

class InstructionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructionTemplate
        fields = ['id', 'category', 'text']
        def validate(self, attrs):
            template_id = self.initial_data.get("instruction_template_id")

            if template_id:
                try:
                    template = InstructionTemplate.objects.get(id=template_id)
                    template.increment_usage()
                except InstructionTemplate.DoesNotExist:
                    pass

            return attrs
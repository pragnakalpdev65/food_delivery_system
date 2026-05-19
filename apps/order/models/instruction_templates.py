from django.db import models
from common.models.base import UUIDModel,TimestampedModel
from apps.core.constants.choices import InstructionCategory

class InstructionTemplate(UUIDModel,TimestampedModel):
    category = models.CharField(max_length=20,choices=InstructionCategory.choices)
    text = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-usage_count', '-created_at']
        
    def __str__(self):
        return self.text
    
    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        self.refresh_from_db(fields=['usage_count'])
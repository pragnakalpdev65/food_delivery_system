from django.db import models
import uuid

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="When this record was created")
    updated_at = models.DateTimeField(auto_now=True, db_index=True, help_text="When this record was last updated")
    deleted_at = models.DateTimeField( null=True, blank=True, db_index=True, help_text="When this record was deleted")
    is_deleted = models.BooleanField( default=False)

    class Meta:
        abstract = True
        
class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier (UUID)",)

    class Meta:
        abstract = True
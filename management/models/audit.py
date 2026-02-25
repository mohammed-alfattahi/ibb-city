"""
Audit & Versioning Models
نماذج التدقيق والإصدارات
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from ibb_guide.base_models import TimeStampedModel


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_logs', verbose_name="المستخدم")
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=50) 
    
    # Snapshot Data
    diff = models.JSONField(default=dict, blank=True, null=True, verbose_name="الفروقات")
    old_values = models.JSONField(default=dict, blank=True, null=True)
    new_values = models.JSONField(default=dict, blank=True, null=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    reason = models.TextField(blank=True, verbose_name="سبب القرار")
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.action} on {self.table_name} by {self.user}"


class GeneralGuideline(TimeStampedModel):
    title = models.CharField(max_length=150)
    content = models.TextField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.title


class ErrorLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    error_message = models.TextField()
    traceback = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Error at {self.path} ({self.timestamp})"


class EntityVersion(TimeStampedModel):
    """
    Soft Versioning Model - Stores snapshots of entities before modifications.
    """
    # Generic link to the versioned object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Version Data
    version_number = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField(help_text="Complete JSON snapshot of the entity at this version")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_versions'
    )
    reason = models.CharField(max_length=200, blank=True, help_text="Reason for this version")
    
    # Link to Request (if applicable)
    related_request = models.ForeignKey(
        'management.Request', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='versions'
    )
    
    class Meta:
        verbose_name = "إصدار الكيان"
        verbose_name_plural = "إصدارات الكيانات"
        ordering = ['-created_at', '-version_number']
        unique_together = ['content_type', 'object_id', 'version_number']
    
    def __str__(self):
        return f"{self.content_type.model} #{self.object_id} - v{self.version_number}"
    
    @classmethod
    def create_snapshot(cls, obj, user=None, reason="", related_request=None):
        """Create a new version snapshot of an object."""
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        content_type = ContentType.objects.get_for_model(obj)
        
        # Get next version number
        last_version = cls.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).order_by('-version_number').first()
        
        next_version = (last_version.version_number + 1) if last_version else 1
        
        # Create snapshot of all fields
        snapshot_data = {}
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif hasattr(value, 'pk'):
                value = value.pk
            else:
                try:
                    json.dumps(value, cls=DjangoJSONEncoder)
                except (TypeError, ValueError):
                    value = str(value)
            snapshot_data[field.name] = value
        
        return cls.objects.create(
            content_type=content_type,
            object_id=obj.pk,
            version_number=next_version,
            snapshot=snapshot_data,
            created_by=user,
            reason=reason,
            related_request=related_request
        )
    
    @classmethod
    def get_versions(cls, obj):
        """Get all versions of an object."""
        content_type = ContentType.objects.get_for_model(obj)
        return cls.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        ).order_by('-version_number')
    
    def rollback(self, user=None):
        """Rollback the target object to this version's snapshot."""
        target = self.content_object
        if not target:
            return False, "Target object no longer exists."
        
        # Create a snapshot of current state before rollback
        EntityVersion.create_snapshot(
            target, 
            user=user, 
            reason=f"Before rollback to v{self.version_number}"
        )
        
        # Apply snapshot values
        for field, value in self.snapshot.items():
            if field in ['id', 'pk', 'created_at', 'updated_at']:
                continue
            if hasattr(target, field):
                try:
                    setattr(target, field, value)
                except Exception:
                    pass
        
        target.save()
        return True, f"Rolled back to version {self.version_number}"

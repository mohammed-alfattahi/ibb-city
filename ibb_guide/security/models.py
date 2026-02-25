"""
Security Models
Provides audit logging for file operations.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel


class FileAuditLog(TimeStampedModel):
    """
    Audit log for file operations (upload, download, delete).
    Tracks who did what with which file.
    """
    
    ACTION_CHOICES = [
        ('upload', _('Upload')),
        ('download', _('Download')),
        ('delete', _('Delete')),
        ('access_denied', _('Access Denied')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='file_audit_logs',
        verbose_name=_('User')
    )
    
    # What action
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        verbose_name=_('Action')
    )
    
    # File info
    file_path = models.CharField(max_length=500, verbose_name=_('File Path'))
    file_name = models.CharField(max_length=255, verbose_name=_('File Name'))
    file_type = models.CharField(max_length=100, blank=True, verbose_name=_('File Type'))
    file_size = models.PositiveIntegerField(null=True, verbose_name=_('File Size (bytes)'))
    
    # Related entity
    entity_type = models.CharField(max_length=100, blank=True, verbose_name=_('Entity Type'))
    entity_id = models.CharField(max_length=100, blank=True, verbose_name=_('Entity ID'))
    
    # Request info
    ip_address = models.GenericIPAddressField(null=True, verbose_name=_('IP Address'))
    user_agent = models.TextField(blank=True, verbose_name=_('User Agent'))
    
    # Additional context
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    success = models.BooleanField(default=True, verbose_name=_('Success'))
    
    class Meta:
        app_label = 'management'  # Use existing app for migrations
        verbose_name = _('File Audit Log')
        verbose_name_plural = _('File Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
    
    def __str__(self):
        return f"[{self.action}] {self.file_name} by {self.user}"
    
    @classmethod
    def log_upload(cls, user, file, entity_type='', entity_id='', ip=None, **kwargs):
        """Log a file upload action."""
        return cls.objects.create(
            user=user,
            action='upload',
            file_path=getattr(file, 'name', str(file)),
            file_name=getattr(file, 'name', 'unknown').split('/')[-1],
            file_type=getattr(file, 'content_type', ''),
            file_size=getattr(file, 'size', None),
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else '',
            ip_address=ip,
            **kwargs
        )
    
    @classmethod
    def log_download(cls, user, file_path, ip=None, **kwargs):
        """Log a file download action."""
        return cls.objects.create(
            user=user,
            action='download',
            file_path=file_path,
            file_name=file_path.split('/')[-1],
            ip_address=ip,
            **kwargs
        )
    
    @classmethod
    def log_delete(cls, user, file_path, ip=None, **kwargs):
        """Log a file deletion action."""
        return cls.objects.create(
            user=user,
            action='delete',
            file_path=file_path,
            file_name=file_path.split('/')[-1],
            ip_address=ip,
            **kwargs
        )
    
    @classmethod
    def log_access_denied(cls, user, file_path, ip=None, **kwargs):
        """Log an access denied event."""
        return cls.objects.create(
            user=user,
            action='access_denied',
            file_path=file_path,
            file_name=file_path.split('/')[-1],
            ip_address=ip,
            success=False,
            **kwargs
        )

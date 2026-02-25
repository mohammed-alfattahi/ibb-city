"""
Notification Outbox Model
Transactional outbox pattern for reliable async notification delivery
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ibb_guide.base_models import TimeStampedModel


class NotificationOutbox(TimeStampedModel):
    """
    Transactional outbox for reliable notification delivery.
    Stores notifications to be processed asynchronously by Celery.
    """
    
    CHANNEL_CHOICES = [
        ('push', _('Push Notification')),
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('in_app', _('In-App')),
    ]
    
    PROVIDER_CHOICES = [
        ('onesignal', 'OneSignal'),
        ('fcm', 'Firebase Cloud Messaging'),
        ('email', 'Email'),
        ('none', 'None'),
    ]
    
    STATUS_CHOICES = [
        ('queued', _('Queued')),
        ('sent', _('Sent')),
        ('failed', _('Failed')),
        ('retrying', _('Retrying')),
        ('dead', _('Dead Letter')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_outbox',
        verbose_name=_('Recipient')
    )
    
    # Channel & Provider
    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default='push',
        verbose_name=_('Channel')
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='fcm',
        verbose_name=_('Provider')
    )
    
    # Content
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    body = models.TextField(verbose_name=_('Body'))
    payload = models.JSONField(default=dict, blank=True, verbose_name=_('Payload'))
    
    # Delivery Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='queued',
        db_index=True,
        verbose_name=_('Status')
    )
    attempts = models.PositiveIntegerField(default=0, verbose_name=_('Attempts'))
    max_attempts = models.PositiveIntegerField(default=5, verbose_name=_('Max Attempts'))
    last_error = models.TextField(blank=True, null=True, verbose_name=_('Last Error'))
    
    # Timestamps
    scheduled_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Scheduled At')
    )
    sent_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name=_('Sent At')
    )
    
    # Optional: Link to related object
    related_object_type = models.CharField(max_length=100, blank=True, null=True)
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Notification Outbox')
        verbose_name_plural = _('Notification Outbox')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['recipient', 'status']),
        ]
    
    def __str__(self):
        return f"[{self.status}] {self.title} → {self.recipient}"
    
    def mark_sent(self):
        """Mark notification as successfully sent."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_failed(self, error_message: str):
        """Mark notification as failed and increment attempts."""
        self.attempts += 1
        self.last_error = error_message
        
        if self.attempts >= self.max_attempts:
            self.status = 'dead'
        else:
            self.status = 'retrying'
        
        self.save(update_fields=['status', 'attempts', 'last_error', 'updated_at'])
    
    def reset_for_retry(self):
        """Reset notification for manual retry."""
        self.status = 'queued'
        self.last_error = None
        self.save(update_fields=['status', 'last_error', 'updated_at'])
    
    @property
    def retry_countdown(self) -> int:
        """Calculate retry countdown with exponential backoff (30s to 1h max)."""
        return min(2 ** self.attempts * 30, 3600)

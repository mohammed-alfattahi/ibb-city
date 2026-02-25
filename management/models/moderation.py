"""
Moderation Models
Content moderation, banned words, and event logs.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel

User = get_user_model()


class BannedWord(TimeStampedModel):
    """
    List of banned or flagged words/phrases.
    """
    SEVERITY_CHOICES = [
        ('low', _('Low (Warning)')),
        ('medium', _('Medium (Review/Flag)')),
        ('high', _('High (Block)')),
    ]
    
    LANGUAGE_CHOICES = [
        ('ar', _('Arabic')),
        ('en', _('English')),
        ('any', _('Any')),
    ]
    
    term = models.CharField(max_length=100, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='any')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Banned Word')
        verbose_name_plural = _('Banned Words')
        ordering = ['term']
        indexes = [
            models.Index(fields=['is_active', 'severity']),
            models.Index(fields=['language', 'is_active']),
        ]
        unique_together = ('term', 'language')

    def __str__(self):
        return f"{self.term} ({self.get_severity_display()})"


class ModerationEvent(models.Model):
    """
    Log of moderation actions (warnings, blocks).
    """
    ACTION_CHOICES = [
        ('warned', _('Warned')),
        ('blocked', _('Blocked')),
        ('flagged', _('Flagged for Review')),
        ('allowed', _('Allowed')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    content_snapshot = models.TextField(_('Flagged Content'))
    matched_terms = models.JSONField(default=list)
    severity = models.CharField(max_length=20)
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Moderation Event')
        verbose_name_plural = _('Moderation Events')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['action_taken']),
        ]

    def __str__(self):
        return f"{self.action_taken} - {self.user or 'Anon'} ({self.created_at})"


class ModerationRule(TimeStampedModel):
    """
    Advanced automatic content moderation rules.
    Moved from interactions.
    """
    ACTION_CHOICES = [
        ('block', _('Block/Auto-Reject')),
        ('flag', _('Flag for Review')),
        ('allow', _('Allow/Auto-Approve')),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_('Rule Name'))
    keywords = models.TextField(
        help_text=_('Comma-separated list of keywords. If any match, the action is triggered.'),
        blank=True
    )
    is_regex = models.BooleanField(default=False, verbose_name=_('Is Regex Pattern?'))
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='flag')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_moderation_rules'
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_action_display()})"


class ModerationQueueItem(TimeStampedModel):
    """
    Queue for manual content moderation.
    Moved from interactions.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    content_snippet = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    flagged_reason = models.CharField(max_length=255, blank=True)
    
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='moderated_items'
    )
    moderation_note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
        
    def __str__(self):
        return f"Moderation Item {self.pk} - {self.status}"

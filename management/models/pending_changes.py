"""
Pending Change Models
نماذج التغييرات المعلقة للموافقة

This module implements field-level approval for partner changes.
Changes to sensitive fields (name, description) require tourism office approval
before appearing publicly.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel


class PendingChange(TimeStampedModel):
    """
    Tracks field-level changes requiring admin approval.
    
    Design Decision: Using direct FK to Establishment rather than GenericForeignKey
    because:
    1. Current scope is establishment-only
    2. Simpler queries and better database referential integrity
    3. Can add additional FK fields for other entity types if needed later
    
    Workflow:
    1. Partner submits change to name/description
    2. PendingChange is created with status='pending'
    3. Admin approves/rejects via admin dashboard
    4. On approval: Establishment is updated, partner notified
    5. On rejection: Partner notified with reason
    """
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name=_('المعرف')
    )
    
    # Entity Type - for future extensibility
    ENTITY_TYPES = [
        ('establishment', _('منشأة')),
    ]
    entity_type = models.CharField(
        max_length=50, 
        choices=ENTITY_TYPES, 
        default='establishment',
        verbose_name=_('نوع الكيان')
    )
    
    # Direct FK to Establishment (simpler than GenericForeignKey for this scope)
    establishment = models.ForeignKey(
        'places.Establishment',
        on_delete=models.CASCADE,
        related_name='pending_changes',
        verbose_name=_('المنشأة')
    )
    
    # Field being changed
    FIELD_CHOICES = [
        ('name', _('الاسم')),
        ('description', _('الوصف')),
    ]
    field_name = models.CharField(
        max_length=50, 
        choices=FIELD_CHOICES,
        verbose_name=_('اسم الحقل')
    )
    
    # Values
    old_value = models.TextField(verbose_name=_('القيمة القديمة'))
    new_value = models.TextField(verbose_name=_('القيمة الجديدة'))
    
    # Request metadata
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_changes',
        verbose_name=_('طلب بواسطة')
    )
    
    # Status tracking
    STATUS_CHOICES = [
        ('pending', _('قيد المراجعة')),
        ('approved', _('موافق عليه')),
        ('rejected', _('مرفوض')),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name=_('الحالة')
    )
    
    # Review metadata
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_changes',
        verbose_name=_('راجع بواسطة')
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('تاريخ المراجعة')
    )
    review_note = models.TextField(
        blank=True,
        verbose_name=_('ملاحظة المراجعة')
    )
    
    # Audit fields
    client_ip = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name=_('عنوان IP')
    )
    
    class Meta:
        verbose_name = _('تغيير معلق')
        verbose_name_plural = _('تغييرات معلقة')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['establishment', 'status']),
            models.Index(fields=['requested_by']),
        ]
    
    def __str__(self):
        return f"{self.get_field_name_display()} - {self.establishment.name} ({self.get_status_display()})"
    
    @property
    def diff_summary(self) -> str:
        """Return a readable summary of the change."""
        old_preview = self.old_value[:50] + '...' if len(self.old_value) > 50 else self.old_value
        new_preview = self.new_value[:50] + '...' if len(self.new_value) > 50 else self.new_value
        return f"{self.get_field_name_display()}: '{old_preview}' → '{new_preview}'"
    
    @property
    def is_pending(self) -> bool:
        return self.status == 'pending'
    
    @property
    def is_approved(self) -> bool:
        return self.status == 'approved'
    
    @property
    def is_rejected(self) -> bool:
        return self.status == 'rejected'
    
    def get_status_badge_class(self) -> str:
        """Return CSS class for status badge."""
        classes = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
        }
        return classes.get(self.status, 'secondary')
    
    def get_status_icon(self) -> str:
        """Return FontAwesome icon for status."""
        icons = {
            'pending': 'fa-clock',
            'approved': 'fa-check-circle',
            'rejected': 'fa-times-circle',
        }
        return icons.get(self.status, 'fa-question-circle')

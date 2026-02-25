"""
Request Models
نماذج الطلبات والموافقات
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from ibb_guide.base_models import TimeStampedModel


class Request(TimeStampedModel):
    REQUEST_TYPES = [
        ('UPGRADE_PARTNER', 'ترقية للشريك'),
        ('ADD_PLACE', 'إضافة مكان جديد'),
        ('UPDATE_INFO', 'تحديث معلومات'),
        ('EDIT_NAME', 'تعديل الاسم'),
        ('EDIT_DESC', 'تعديل الوصف'),
        ('EDIT_LOCATION', 'تعديل الموقع'),
        ('EDIT_CATEGORY', 'تعديل التصنيف'),
        ('EDIT_MEDIA', 'تعديل الصور/الفيديو'),
        ('VERIFY_ESTABLISHMENT', 'طلب توثيق'),
        ('CREATE_AD', 'إنشاء إعلان'),
        ('OTHER', 'أخرى'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('NEEDS_INFO', 'Needs Info'),
        ('CONDITIONAL_APPROVAL', 'Conditional Approval'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests')
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    
    # Generic link to the target object (Establishment, Profile, etc.)
    target_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Data Changes
    changes = models.JSONField(default=dict, blank=True, help_text="Dictionary of field changes {field: new_value}")
    original_data = models.JSONField(default=dict, blank=True, help_text="Snapshot of original data for comparison")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    description = models.TextField(blank=True, help_text="User's description of the request")
    attachment = models.FileField(upload_to='requests/attachments/', blank=True, null=True)
    
    # Admin Response
    admin_response = models.TextField(blank=True, help_text="Admin's response or feedback")
    admin_notes = models.TextField(blank=True, help_text="Private notes for admins")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='reviewed_requests', null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Advanced Approval Fields
    conditions = models.TextField(blank=True, verbose_name="شروط الموافقة")
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="مهلة التعديل")
    decision_doc = models.FileField(upload_to='requests/decisions/', blank=True, null=True, verbose_name="مستند القرار")

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='assigned_requests', 
        null=True, 
        blank=True,
        verbose_name="مسند إلى"
    )
    priority = models.CharField(max_length=20, default='MEDIUM', choices=[('LOW', 'منخفض'), ('MEDIUM', 'متوسط'), ('HIGH', 'عالي')])
    expected_completion_at = models.DateTimeField(null=True, blank=True, help_text="SLA Deadline")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['request_type']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.get_request_type_display()} by {self.user} - {self.get_status_display()}"
    
    def get_status_message(self) -> str:
        """Return user-friendly Arabic message for current status."""
        messages = {
            'PENDING': '🕐 طلبك قيد المراجعة من الإدارة. يرجى الانتظار.',
            'APPROVED': '✅ تمت الموافقة على طلبك وتم تطبيق التعديلات.',
            'REJECTED': f'❌ تم رفض طلبك. السبب: {self.admin_response or "لم يتم تحديد سبب"}',
            'NEEDS_INFO': f'📝 مطلوب معلومات إضافية: {self.admin_response or "يرجى التواصل مع الإدارة"}',
            'CONDITIONAL_APPROVAL': f'⚠️ تمت الموافقة المشروطة. الشروط: {self.conditions or "راجع التفاصيل"}',
        }
        return messages.get(self.status, 'حالة غير معروفة')
    
    def get_timeline(self):
        """Return status history timeline for this request."""
        return self.status_logs.all().order_by('created_at')
    
    @property
    def status_badge_class(self) -> str:
        """Return CSS class for status badge."""
        classes = {
            'PENDING': 'badge-warning',
            'APPROVED': 'badge-success',
            'REJECTED': 'badge-danger',
            'NEEDS_INFO': 'badge-info',
            'CONDITIONAL_APPROVAL': 'badge-warning',
        }
        return classes.get(self.status, 'badge-secondary')


class ApprovalAssignment(models.Model):
    """Log of who was assigned to a request and when."""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='task_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.request} -> {self.assigned_to}"


class RequestStatusLog(TimeStampedModel):
    """Track status changes for requests - provides a timeline for user feedback."""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='status_changes'
    )
    message = models.TextField(blank=True, help_text="Message shown to user")
    internal_note = models.TextField(blank=True, help_text="Internal admin note")
    
    class Meta:
        verbose_name = "سجل حالة الطلب"
        verbose_name_plural = "سجلات حالات الطلبات"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request} - {self.from_status} → {self.to_status}"
    
    @classmethod
    def log_status_change(cls, request, new_status, changed_by, message="", internal_note=""):
        """Log a status change for a request."""
        return cls.objects.create(
            request=request,
            from_status=request.status,
            to_status=new_status,
            changed_by=changed_by,
            message=message,
            internal_note=internal_note
        )
    
    def get_status_icon(self) -> str:
        """Return appropriate icon for the status."""
        icons = {
            'PENDING': '🕐',
            'APPROVED': '✅',
            'REJECTED': '❌',
            'NEEDS_INFO': '📝',
            'CONDITIONAL_APPROVAL': '⚠️',
        }
        return icons.get(self.to_status, '📌')


class ApprovalDecision(TimeStampedModel):
    """Formal approval decision record."""
    DECISION_TYPES = [
        ('APPROVE', 'موافقة'),
        ('REJECT', 'رفض'),
        ('REQUEST_INFO', 'طلب معلومات'),
        ('CONDITIONAL', 'موافقة مشروطة'),
        ('REVOKE', 'إلغاء'),
    ]
    
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='decisions')
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='approval_decisions'
    )
    decision = models.CharField(max_length=20, choices=DECISION_TYPES)
    reason = models.TextField(help_text="سبب القرار")
    conditions = models.TextField(blank=True, help_text="الشروط (للموافقة المشروطة)")
    deadline = models.DateTimeField(null=True, blank=True, help_text="مهلة التنفيذ")
    decision_document = models.FileField(
        upload_to='decisions/documents/', 
        blank=True, 
        null=True,
        help_text="مستند القرار الرسمي"
    )
    is_final = models.BooleanField(default=True, help_text="قرار نهائي")
    
    class Meta:
        verbose_name = "قرار الموافقة"
        verbose_name_plural = "قرارات الموافقات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request', 'decision']),
            models.Index(fields=['decided_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_decision_display()} - {self.request} by {self.decided_by}"
    
    @classmethod
    def record_decision(cls, request, user, decision: str, reason: str, 
                        conditions: str = "", deadline=None, document=None):
        """Record a formal approval decision."""
        return cls.objects.create(
            request=request,
            decided_by=user,
            decision=decision,
            reason=reason,
            conditions=conditions,
            deadline=deadline,
            decision_document=document
        )
    
    def get_decision_icon(self) -> str:
        """Get icon for decision type."""
        icons = {
            'APPROVE': '✅',
            'REJECT': '❌',
            'REQUEST_INFO': '📝',
            'CONDITIONAL': '⚠️',
            'REVOKE': '🚫',
        }
        return icons.get(self.decision, '📋')

"""
Report Models
نماذج البلاغات
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from ibb_guide.base_models import TimeStampedModel


class Report(TimeStampedModel):
    """نموذج البلاغات مع تتبع الأولوية والتخصيص والحل"""
    
    REPORT_TYPES = [
        ('INACCURATE', 'معلومات غير دقيقة'),
        ('SPAM', 'محتوى مزعج'),
        ('INAPPROPRIATE', 'محتوى غير لائق'),
        ('SAFETY', 'مخاطر أمنية'),
        ('COPYRIGHT', 'انتهاك حقوق ملكية'),
        ('OTHER', 'أخرى'),
    ]
    
    REPORT_STATUS = [
        ('NEW', 'جديد'),
        ('IN_PROGRESS', 'قيد المعالجة'),
        ('PENDING_INFO', 'بانتظار معلومات'),
        ('RESOLVED', 'تم الحل'),
        ('REJECTED', 'مرفوض'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
        ('critical', 'حرجة'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reports')
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='OTHER')
    status = models.CharField(max_length=20, choices=REPORT_STATUS, default='NEW')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='الأولوية')
    
    proof_image = models.ImageField(upload_to='reports/proofs/', blank=True, null=True)
    description = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='assigned_reports',
        verbose_name='مُسند إلى'
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الحل')
    expected_resolution_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الحل المتوقع (SLA)')
    resolution_note = models.TextField(blank=True, verbose_name='ملاحظات الحل')

    class Meta:
        app_label = 'interactions'
        ordering = ['-created_at']
        verbose_name = 'بلاغ'
        verbose_name_plural = 'البلاغات'

    def __str__(self):
        return f"Report {self.id} by {self.user}"
    
    def assign_to(self, admin_user):
        self.assigned_to = admin_user
        self.status = 'IN_PROGRESS'
        self.save(update_fields=['assigned_to', 'status'])
    
    def resolve(self, note=''):
        from django.utils import timezone
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        if note:
            self.resolution_note = note
        self.save(update_fields=['status', 'resolved_at', 'resolution_note'])
        self._notify_reporter()
    
    def reject(self, note=''):
        self.status = 'REJECTED'
        if note:
            self.admin_note = note
        self.save(update_fields=['status', 'admin_note'])
        self._notify_reporter()
    
    def _notify_reporter(self):
        from .notifications import Notification
        if not self.user:
            return
        
        if self.status == 'RESOLVED':
            notification_type = 'report_resolved'
            title = 'تم حل بلاغك'
            message = f'تم معالجة بلاغك رقم #{self.id} بنجاح.'
        else:
            notification_type = 'report_rejected'
            title = 'تحديث على بلاغك'
            message = f'تم مراجعة بلاغك رقم #{self.id}.'
        
        Notification.objects.create(
            recipient=self.user,
            notification_type=notification_type,
            title=title,
            message=message
        )

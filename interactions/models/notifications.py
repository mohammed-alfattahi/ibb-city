"""
Notification Models
نماذج الإشعارات وتفضيلاتها
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from ibb_guide.base_models import TimeStampedModel


class Notification(TimeStampedModel):
    """نموذج الإشعارات الشامل مع التتبع الكامل"""
    
    NOTIFICATION_TYPES = [
        # إشعارات الشريك
        ('partner_approved', 'تم اعتماد حسابك كشريك'),
        ('partner_rejected', 'تم رفض طلب الشراكة'),
        ('partner_needs_info', 'مطلوب معلومات إضافية'),
        ('establishment_approved', 'تم قبول المنشأة'),
        ('establishment_rejected', 'تم رفض المنشأة'),
        ('establishment_suspended', 'تم إيقاف المنشأة'),
        ('establishment_reactivated', 'تم إعادة تفعيل المنشأة'),
        ('ad_approved', 'تم قبول الإعلان'),
        ('ad_rejected', 'تم رفض الإعلان'),
        ('ad_payment_needed', 'مطلوب رفع سند الدفع'),
        ('ad_expiring_soon', 'الإعلان قارب على الانتهاء'),
        ('ad_expired', 'انتهى الإعلان'),
        ('new_review', 'تعليق جديد على منشأتك'),
        ('new_report_on_establishment', 'بلاغ جديد على منشأتك'),
        # إشعارات التغييرات المعلقة (Field-Level Approval)
        ('pending_change_requested', 'طلب تغيير معلق'),
        ('pending_change_approved', 'تمت الموافقة على التغيير'),
        ('pending_change_rejected', 'تم رفض التغيير'),
        ('partner_field_update', 'تحديث حقل المنشأة'),
        # إشعارات مكتب السياحة
        ('new_partner_registration', 'تسجيل شريك جديد'),
        ('partner_upgrade_request', 'طلب ترقية حساب لشريك'),
        ('new_establishment_request', 'طلب منشأة جديدة'),
        ('establishment_update_request', 'طلب تحديث منشأة'),
        ('new_ad_request', 'طلب إعلان جديد'),
        ('review_objection', 'اعتراض على مراجعة'),
        ('new_user_report', 'بلاغ جديد من مستخدم'),
        # إشعارات السائح
        ('review_reply', 'رد على تعليقك'),
        ('report_update', 'تحديث على بلاغك'),
        ('report_resolved', 'تم حل بلاغك'),
        ('report_rejected', 'تم رفض بلاغك'),
        ('favorite_suspended', 'تم إيقاف منشأة محفوظة'),
        ('favorite_reactivated', 'تم إعادة تفعيل منشأة محفوظة'),
        ('favorite_new_offer', 'عرض جديد على منشأة محفوظة'),
        ('weather_alert', 'تنبيه طقس'),
        ('general', 'إشعار عام'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name='المستلم',
        null=True
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='sent_notifications',
        verbose_name='المرسل',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES,
        verbose_name='نوع الإشعار',
        default='general'
    )
    event_type = models.CharField(max_length=100, blank=True, verbose_name='نوع الحدث')
    
    title = models.CharField(max_length=200, verbose_name='العنوان', default='إشعار جديد')
    message = models.TextField(verbose_name='الرسالة', default='')
    
    priority = models.CharField(
        max_length=20,
        choices=[('high', 'High'), ('normal', 'Normal'), ('low', 'Low')],
        default='normal'
    )
    
    metadata = models.JSONField(default=dict, blank=True, null=True)
    
    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ القراءة')
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    action_url = models.CharField(max_length=500, blank=True, verbose_name='رابط الإجراء')
    
    class Meta:
        app_label = 'interactions'
        ordering = ['-created_at']
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.recipient.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class SystemAlert(TimeStampedModel):
    """
    نموذج لتنبيهات النظام والبث العام.
    يستخدم من لوحة الإدارة لإرسال إشعارات جماعية.
    """
    ALERT_TYPES = [
        ('WEATHER_ALERT', 'تنبيه طقس'),
        ('SYSTEM_ALERT', 'تنبيه نظام'),
        ('STAFF_ALERT', 'تنبيه إداري'),
    ]
    
    AUDIENCE_CHOICES = [
        ('all', 'الجميع (بث عام)'),
        ('partners', 'الشركاء فقط'),
        ('staff', 'المشرفين فقط'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='عنوان التنبيه')
    message = models.TextField(verbose_name='نص الرسالة')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES, default='SYSTEM_ALERT', verbose_name='نوع التنبيه')
    target_audience = models.CharField(max_length=50, choices=AUDIENCE_CHOICES, default='all', verbose_name='الجمهور المستهدف')
    
    is_sent = models.BooleanField(default=False, verbose_name='تم الإرسال')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ الإرسال')
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='أنشئ بواسطة'
    )

    class Meta:
        app_label = 'interactions'
        verbose_name = 'تنبيه جماعي / طقس'
        verbose_name_plural = 'التنبيهات الجماعية'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"


class NotificationPreference(TimeStampedModel):
    """تفضيلات إشعارات المستخدم"""
    
    CATEGORY_CHOICES = [
        ('approvals', 'الموافقات والقرارات'),
        ('reviews', 'التعليقات والتقييمات'),
        ('ads', 'الإعلانات'),
        ('system', 'إشعارات النظام'),
        ('weather', 'تنبيهات الطقس'),
        ('promotions', 'العروض والترويج'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    enable_all = models.BooleanField(default=True, verbose_name='تفعيل جميع الإشعارات')
    enable_push = models.BooleanField(default=True, verbose_name='إشعارات الدفع')
    enable_email = models.BooleanField(default=False, verbose_name='إشعارات البريد الإلكتروني')
    enable_sms = models.BooleanField(default=False, verbose_name='إشعارات الرسائل النصية')
    
    disabled_categories = models.JSONField(default=dict, blank=True, verbose_name='الفئات المعطلة')
    disabled_types = models.JSONField(default=list, blank=True, verbose_name='الأنواع المعطلة')
    
    quiet_hours_enabled = models.BooleanField(default=False, verbose_name='تفعيل ساعات الهدوء')
    quiet_start = models.TimeField(null=True, blank=True, verbose_name='بداية ساعات الهدوء')
    quiet_end = models.TimeField(null=True, blank=True, verbose_name='نهاية ساعات الهدوء')
    
    class Meta:
        app_label = 'interactions'
        verbose_name = 'تفضيلات الإشعارات'
        verbose_name_plural = 'تفضيلات الإشعارات'
    
    def __str__(self):
        return f"Notification Preferences for {self.user.username}"
    
    def is_notification_enabled(self, notification_type: str) -> bool:
        if not self.enable_all:
            return False
        if self.quiet_hours_enabled and self._is_quiet_time():
            return False
        if notification_type in self.disabled_types:
            return False
        category = self._get_category_for_type(notification_type)
        if category and category in self.disabled_categories:
            return False
        return True
    
    def _is_quiet_time(self) -> bool:
        if not self.quiet_start or not self.quiet_end:
            return False
        from datetime import datetime
        now = datetime.now().time()
        if self.quiet_start <= self.quiet_end:
            return self.quiet_start <= now <= self.quiet_end
        else:
            return now >= self.quiet_start or now <= self.quiet_end
    
    def _get_category_for_type(self, notification_type: str) -> str:
        type_to_category = {
            'partner_approved': 'approvals', 'partner_rejected': 'approvals',
            'establishment_approved': 'approvals', 'establishment_rejected': 'approvals',
            'new_establishment_request': 'approvals', 'establishment_update_request': 'approvals',
            'new_review': 'reviews', 'new_report_on_establishment': 'reviews',
            'ad_approved': 'ads', 'ad_rejected': 'ads', 'ad_expiring_soon': 'ads',
            'weather_alert': 'weather', 'system_update': 'system',
        }
        return type_to_category.get(notification_type, 'system')
    
    @classmethod
    def get_or_create_for_user(cls, user):
        prefs, created = cls.objects.get_or_create(user=user)
        return prefs

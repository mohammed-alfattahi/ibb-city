"""
Landmark & ServicePoint Models
نماذج المعالم ونقاط الخدمات
"""
from django.db import models
from django.conf import settings
from .base import Place


class Landmark(Place):
    """Tourism landmarks managed by Tourism Office."""
    
    LANDMARK_TYPES = [
        ('historical', 'تاريخي'),
        ('natural', 'طبيعي'),
        ('religious', 'ديني'),
        ('archaeological', 'أثري'),
        ('cultural', 'ثقافي'),
        ('other', 'أخرى'),
    ]
    
    landmark_type = models.CharField(max_length=100, choices=LANDMARK_TYPES, blank=True)
    safety_instructions = models.TextField(blank=True, verbose_name="تعليمات السلامة")
    best_visit_time = models.CharField(max_length=100, blank=True, verbose_name="أفضل وقت للزيارة")
    climate_description = models.TextField(blank=True, verbose_name="وصف المناخ")
    photography_rules = models.TextField(blank=True, verbose_name="ضوابط التصوير")
    
    is_verified = models.BooleanField(default=False, verbose_name="موثق من مكتب السياحة")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_landmarks',
        verbose_name="موثق بواسطة"
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ التوثيق")
    verification_notes = models.TextField(blank=True, verbose_name="ملاحظات التوثيق")
    
    official_classification = models.CharField(max_length=100, blank=True, verbose_name="التصنيف الرسمي")
    historical_period = models.CharField(max_length=100, blank=True, verbose_name="الفترة التاريخية")
    estimated_age = models.CharField(max_length=100, blank=True, verbose_name="العمر التقريبي")
    conservation_status = models.CharField(max_length=50, blank=True, verbose_name="حالة الحفاظ")
    unesco_listed = models.BooleanField(default=False, verbose_name="مدرج في يونسكو")
    
    @property
    def is_tourism_verified(self) -> bool:
        return self.is_verified and self.verified_by is not None
    
    @property
    def verification_badge_class(self) -> str:
        return 'badge-tourism-verified' if self.is_verified else ''

    def __str__(self):
        return f"{self.name} (Landmark)"
    
    class Meta:
        verbose_name = "معلم سياحي"
        verbose_name_plural = "المعالم السياحية"


class ServicePoint(Place):
    """Auxiliary services like banks, restrooms, mosques."""
    
    SERVICE_TYPES = [
        ('bank', 'بنك / صرافة'),
        ('atm', 'صراف آلي'),
        ('car_rental', 'تأجير سيارات'),
        ('restroom', 'دورة مياه'),
        ('mosque', 'مسجد'),
        ('parking', 'موقف سيارات'),
        ('hospital', 'مستشفى / مركز صحي'),
        ('pharmacy', 'صيدلية'),
        ('police', 'مركز شرطة'),
        ('gas_station', 'محطة وقود'),
    ]
    
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, verbose_name="نوع الخدمة")
    is_24_hours = models.BooleanField(default=False, verbose_name="يعمل 24 ساعة")
    has_disabled_access = models.BooleanField(default=False, verbose_name="مجهز لذوي الهمم")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="رقم الهاتف")
    website = models.URLField(blank=True, verbose_name="الموقع الإلكتروني")
    
    class Meta:
        verbose_name = "نقطة خدمة"
        verbose_name_plural = "نقاط الخدمات"

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"
    
    @property
    def icon_class(self):
        icons = {
            'bank': 'fa-money-bill-wave', 'atm': 'fa-money-check-dollar',
            'car_rental': 'fa-car', 'restroom': 'fa-restroom',
            'mosque': 'fa-mosque', 'parking': 'fa-parking',
            'hospital': 'fa-hospital', 'pharmacy': 'fa-pills',
            'police': 'fa-shield-halved', 'gas_station': 'fa-gas-pump',
        }
        return icons.get(self.service_type, 'fa-map-pin')

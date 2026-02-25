"""
Alert Models
نماذج التنبيهات والطوارئ
"""
from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel


class WeatherAlert(TimeStampedModel):
    SEVERITY_CHOICES = [
        ('YELLOW', 'تنبيه أصفر (خفيف)'),
        ('ORANGE', 'تنبيه برتقالي (متوسط)'),
        ('RED', 'تنبيه أحمر (خطر)'),
    ]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='weather_alerts')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    polygon = models.TextField(blank=True, help_text="Polygon coordinates")
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.severity})"


class EmergencyAlert(TimeStampedModel):
    ALERT_TYPES = [
        ('MEDICAL', 'طوارئ طبية'),
        ('SECURITY', 'خطر أمني'),
        ('LOST', 'ضياع'),
        ('WEATHER', 'سيول/طقس'),
        ('ACCIDENT', 'حادث مروري'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'نشط - جاري التعامل'),
        ('RESPONDING', 'تم الاستجابة'),
        ('RESOLVED', 'تم الحل'),
        ('FALSE_ALARM', 'بلاغ خاطئ'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emergency_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Location Data (Critical)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Response Data
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='responded_alerts')
    responded_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    
    metadata = models.JSONField(default=dict, blank=True, help_text="Battery level, signal strength, etc.")

    def __str__(self):
        return f"SOS: {self.get_alert_type_display()} by {self.user} ({self.status})"


class EmergencyContact(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    relation = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number}) for {self.user}"

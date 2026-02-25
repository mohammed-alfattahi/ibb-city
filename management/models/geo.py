"""
Geo & Navigation Models
نماذج الموقع الجغرافي والملاحة
"""
from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel


class VehicleProfile(models.Model):
    TYPE_CHOICES = [
        ('SEDAN', 'سيارة صغيرة (Sedan)'),
        ('SUV', 'سيارة عائلية (SUV)'),
        ('4X4', 'دفع رباعي (4x4)'),
        ('MOTORCYCLE', 'دراجة نارية'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicle_profile')
    vehicle_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SEDAN')
    
    def __str__(self):
        return f"{self.user} - {self.get_vehicle_type_display()}"


class RouteLog(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    destination_place = models.ForeignKey('places.Place', on_delete=models.CASCADE)
    safety_status = models.CharField(max_length=20)  # Safe, Warning, Danger
    warnings = models.JSONField(default=list)
    
    def __str__(self):
        return f"Route to {self.destination_place} ({self.safety_status})"


class GeoZone(TimeStampedModel):
    ZONE_TYPES = [
        ('FLOOD', 'مجاري سيول'),
        ('SECURITY', 'منطقة أمنية'),
        ('RESTRICTED', 'منطقة محظورة'),
        ('DANGEROUS_ROAD', 'طريق خطر'),
    ]
    RISK_LEVELS = [
        ('LOW', 'منخفض'),
        ('MEDIUM', 'متوسط'),
        ('HIGH', 'عالي'),
        ('CRITICAL', 'خطر جداً'),
    ]
    
    name = models.CharField(max_length=150)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    polygon = models.JSONField(help_text="List of [lat, lon] points defining the zone")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_zone_type_display()})"


class UserLocation(models.Model):
    """Last known location of a user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='current_location')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.user} at {self.latitude}, {self.longitude}"

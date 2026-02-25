"""
Base Place Models
نماذج الأماكن الأساسية
"""
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="الاسم")
    icon = models.ImageField(upload_to='categories/icons/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=100, verbose_name="الاسم")
    icon = models.ImageField(upload_to='amenities/icons/', blank=True, null=True)

    def __str__(self):
        return self.name


class Place(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='places', verbose_name="التصنيف")
    name = models.CharField(max_length=200, verbose_name="اسم المكان")
    description = models.TextField(blank=True, verbose_name="الوصف")
    is_active = models.BooleanField(default=True, help_text=_("Designates whether this place should be treated as active."), verbose_name="نشط")
    is_featured = models.BooleanField(default=False, verbose_name="مميز")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="خط العرض")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="خط الطول")
    address_text = models.TextField(blank=True, verbose_name="العنوان التفصيلي")
    cover_image = models.ImageField(upload_to='places/covers/', blank=True, null=True, verbose_name="صورة الغلاف")
    contact_info = models.JSONField(default=dict, blank=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    rating_count = models.PositiveIntegerField(default=0, verbose_name=_('عدد التقييمات'))
    rating_distribution = models.JSONField(default=dict, blank=True, verbose_name=_('توزيع التقييمات'))
    view_count = models.PositiveIntegerField(default=0, verbose_name=_('عدد المشاهدات'))
    
    PRICE_RANGES = [
        ('low', '$ (اقتصادي)'),
        ('medium', '$$ (متوسط)'),
        ('high', '$$$ (فاخر)'),
    ]
    price_range = models.CharField(max_length=20, choices=PRICE_RANGES, default='medium', verbose_name="مستوى الأسعار")
    opening_hours_text = models.CharField(max_length=200, blank=True, verbose_name="ساعات العمل (نص)")
    
    ROAD_CHOICES = [
        ('paved', 'Paved'),
        ('offroad', 'Off-road (4x4)'),
    ]
    CLASSIFICATION_CHOICES = [
        ('general', 'General'),
        ('family', 'Family Only'),
    ]
    road_condition = models.CharField(max_length=20, choices=ROAD_CHOICES, default='paved', blank=True)
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default='general', blank=True)

    DIRECTORATE_CHOICES = [
        ('AL_DHIHAR', 'الظهار'),
        ('AL_MASHANNAH', 'المشنة'),
        ('JIBLA', 'جبلة'),
        ('AL_SADDAH', 'السدة'),
        ('BAADAN', 'بعدان'),
        ('AL_SABRA', 'السبرة'),
        ('AL_UDAYN', 'العدين'),
        ('HAZM_AL_UDAYN', 'حزم العدين'),
        ('FAR_AL_UDAYN', 'فرع العدين'),
        ('HUBISH', 'حبيش'),
        ('AL_MAKHADIR', 'المخادر'),
        ('AL_QAFR', 'القفر'),
        ('YARIM', 'يريم'),
        ('AL_RADMA', 'الرضمة'),
        ('AL_NANIYANI', 'السياني'),
        ('ZI_ALSUFAL', 'ذي السفال'),
        ('AL_MANDAR', 'المندر'),
    ]
    directorate = models.CharField(
        max_length=50, 
        choices=DIRECTORATE_CHOICES, 
        default='AL_DHIHAR',
        verbose_name=_("المديرية"),
        blank=True
    )

    OPERATIONAL_STATUS_CHOICES = [
        ('active', _('نشط ومفتوح')),
        ('closed', _('مغلق مؤقتاً')),
        ('maintenance', _('قيد الصيانة')),
        ('seasonal', _('موسمي')),
        ('dangerous', _('خطر - غير آمن للزيارة')),
    ]
    operational_status = models.CharField(
        max_length=20,
        choices=OPERATIONAL_STATUS_CHOICES,
        default='active',
        verbose_name=_('الحالة التشغيلية')
    )
    status_note = models.TextField(blank=True, verbose_name=_('ملاحظة الحالة'))
    reopening_date = models.DateField(null=True, blank=True, verbose_name=_('تاريخ إعادة الافتتاح المتوقع'))
    
    SEASON_CHOICES = [
        ('all_year', _('طوال العام')),
        ('summer', _('الصيف')),
        ('winter', _('الشتاء')),
        ('spring', _('الربيع')),
        ('rainy', _('موسم الأمطار')),
    ]
    best_season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all_year', verbose_name=_('أفضل موسم للزيارة'))

    def __str__(self):
        return self.name
    
    @property
    def is_visitable(self):
        return self.operational_status in ['active', 'seasonal']
    
    @property
    def has_warning(self):
        return self.operational_status != 'active'
    
    @property
    def status_css_class(self):
        classes = {
            'active': 'success', 'closed': 'warning', 'maintenance': 'info',
            'seasonal': 'primary', 'dangerous': 'danger',
        }
        return classes.get(self.operational_status, 'secondary')
    
    @property
    def status_icon(self):
        icons = {
            'active': 'fa-check-circle', 'closed': 'fa-door-closed',
            'maintenance': 'fa-tools', 'seasonal': 'fa-calendar-alt',
            'dangerous': 'fa-exclamation-triangle',
        }
        return icons.get(self.operational_status, 'fa-info-circle')

    def get_absolute_url(self):
        return reverse('place_detail', args=[str(self.pk)])

    class Meta:
        verbose_name = "مكان"
        verbose_name_plural = "الأماكن"
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['avg_rating']),
            models.Index(fields=['directorate']),
            models.Index(fields=['created_at']),
        ]


class PlaceMedia(models.Model):
    MEDIA_TYPES = [('IMAGE', 'Image'), ('VIDEO', 'Video')]
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='media')
    media_url = models.FileField(upload_to='places/media/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, default='IMAGE')
    is_cover = models.BooleanField(default=False)

    def __str__(self):
        return f"Media for {self.place.name}"

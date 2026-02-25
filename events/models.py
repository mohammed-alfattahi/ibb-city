from django.db import models
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel

class Season(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name=_("اسم الموسم"))
    description = models.TextField(blank=True, verbose_name=_("الوصف"))
    start_date = models.DateField(verbose_name=_("تاريخ البداية"))
    end_date = models.DateField(verbose_name=_("تاريخ النهاية"))
    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    cover_image = models.ImageField(upload_to='seasons/covers/', blank=True, null=True, verbose_name=_("صورة الغلاف"))

    def __str__(self):
        return self.name

class Event(TimeStampedModel):
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True, related_name='events', verbose_name=_("الموسم"))
    title = models.CharField(max_length=200, verbose_name=_("عنوان الفعالية"))
    description = models.TextField(verbose_name=_("الوصف"))
    location = models.CharField(max_length=200, verbose_name=_("الموقع"))
    start_datetime = models.DateTimeField(verbose_name=_("تاريخ ووقت البداية"))
    end_datetime = models.DateTimeField(verbose_name=_("تاريخ ووقت النهاية"))
    cover_image = models.ImageField(upload_to='events/covers/', blank=True, null=True, verbose_name=_("صورة الغلاف"))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("سعر التذكرة"))
    
    EVENT_TYPES = [
        ('festival', _('مهرجان')),
        ('concert', _('حفلة')),
        ('exhibition', _('معرض')),
        ('workshop', _('ورشة عمل')),
        ('sports', _('رياضة')),
        ('tour', _('جولة')),
        ('cultural', _('ثقافي')),
        ('market', _('سوق')),
        ('adventure', _('مغامرة')),
        ('other', _('آخر')),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='other', verbose_name=_("نوع الفعالية"))
    is_featured = models.BooleanField(default=False, verbose_name=_("مميز"))

    def __str__(self):
        return self.title

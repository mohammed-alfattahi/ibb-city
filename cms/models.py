from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class UIZone(models.Model):
    name = models.CharField(_("اسم المنطقة"), max_length=100)
    slug = models.SlugField(unique=True, help_text="e.g., sidebar_right, homepage_main")
    description = models.TextField(blank=True)
    def render_data(self):
        """Merged data for rendering: component.default_data overridden by instance data_override."""
        data = {}
        if getattr(self, 'component_id', None):
            base = getattr(self.component, 'default_data', None) or {}
            if isinstance(base, dict):
                data.update(base)
        override = getattr(self, 'data_override', None) or {}
        if isinstance(override, dict):
            data.update(override)
        return data


    def __str__(self):
        return self.name

class UIComponent(models.Model):
    name = models.CharField(_("اسم العنصر"), max_length=100)
    slug = models.SlugField(unique=True)
    template_path = models.CharField(_("مسار القالب"), max_length=255, help_text="e.g., components/molecules/weather_widget.html")
    default_data = models.JSONField(_("بيانات افتراضية"), default=dict, blank=True)
    
    def __str__(self):
        return self.name

class ZoneComponent(models.Model):
    zone = models.ForeignKey(UIZone, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(UIComponent, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(_("الترتيب"), default=0)
    is_visible = models.BooleanField(_("طاهر"), default=True)
    
    # Draft/Publish support
    STAGE_CHOICES = [
        ('draft', _('مسودة')),
        ('published', _('منشور')),
    ]
    stage = models.CharField(_('المرحلة'), max_length=16, choices=STAGE_CHOICES, default='published', db_index=True)
    data_override = models.JSONField(_('بيانات مخصصة'), default=dict, blank=True)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)
    updated_at = models.DateTimeField(_('تاريخ التحديث'), auto_now=True)
    class Meta:
        ordering = ['order']
        verbose_name = _("مكون المنطقة")
        verbose_name_plural = _("مكونات المنطقة")

    def __str__(self):
        return f"{self.zone.name} - {self.component.name}"


class UIRevision(models.Model):
    """A simple version snapshot for a zone publish/copy operation."""
    zone = models.ForeignKey(UIZone, on_delete=models.CASCADE, related_name='revisions')
    action = models.CharField(_('الإجراء'), max_length=32, default='publish')
    from_stage = models.CharField(_('من مرحلة'), max_length=16, blank=True)
    to_stage = models.CharField(_('إلى مرحلة'), max_length=16, blank=True)
    snapshot = models.JSONField(_('اللقطة'), default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(_('تاريخ الإنشاء'), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('نسخة واجهة')
        verbose_name_plural = _('نسخ الواجهة')

    def __str__(self):
        return f"{self.zone.slug} - {self.action} - {self.created_at:%Y-%m-%d %H:%M}"

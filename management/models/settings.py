from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemSetting(models.Model):
    KEY_CHOICES = [
        ('site_name', _('Site Name')),
        ('maintenance_mode', _('Maintenance Mode')),
        ('allow_registration', _('Allow Registration')),
        ('welcome_message', _('Welcome Message')),
        ('contact_email', _('Contact Email')),
        ('max_upload_size', _('Max Upload Size (MB)')),
    ]

    TYPE_CHOICES = [
        ('string', _('String')),
        ('integer', _('Integer')),
        ('boolean', _('Boolean')),
        ('text', _('Text')),
    ]

    key = models.CharField(max_length=50, unique=True, verbose_name=_('Key'))
    value = models.TextField(verbose_name=_('Value'))
    data_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='string', verbose_name=_('Data Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    is_public = models.BooleanField(default=False, verbose_name=_('Is Public'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('System Setting')
        verbose_name_plural = _('System Settings')
        indexes = [
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"{self.key}: {self.value}"

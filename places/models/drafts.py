from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel

class EstablishmentDraft(TimeStampedModel):
    """
    Stores incomplete wizard data for establishments.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='establishment_drafts')
    establishment = models.ForeignKey('places.Establishment', on_delete=models.CASCADE, null=True, blank=True, related_name='drafts')
    
    # Store field data as JSON
    data = models.JSONField(default=dict, blank=True)
    
    current_step = models.IntegerField(default=1)
    is_create_mode = models.BooleanField(default=True, help_text=_("True if creating new establishment, False if editing"))
    
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('submitted', _('تم الإرسال')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        verbose_name = _('مسودة منشأة')
        verbose_name_plural = _('مسودات المنشآت')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Draft {self.pk} - {self.user}"

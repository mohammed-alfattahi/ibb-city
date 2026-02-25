"""
Follows Models
نماذج المتابعة
"""
from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel

class EstablishmentFollow(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following'
    )
    establishment = models.ForeignKey(
        'places.Establishment',
        on_delete=models.CASCADE,
        related_name='followers'
    )

    class Meta:
        app_label = 'interactions'
        verbose_name = 'متابعة'
        verbose_name_plural = 'المتابعات'
        unique_together = ('user', 'establishment')
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['establishment']),
        ]

    def __str__(self):
        return f"{self.user} follows {self.establishment}"

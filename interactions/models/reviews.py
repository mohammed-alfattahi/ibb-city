"""Review & Comment Models

نماذج التقييمات والتعليقات

تم توحيد منطق الإخفاء/الإظهار عبر حقل visibility_state
لكل من Review و PlaceComment لتفادي تضارب الحقول القديمة (is_hidden/status).
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from ibb_guide.base_models import TimeStampedModel


VISIBILITY_CHOICES = [
    ('visible', _('Visible')),
    ('partner_hidden', _('Hidden by Partner')),
    ('admin_hidden', _('Hidden by Admin')),
]


class Review(TimeStampedModel):
    """نموذج التقييمات (Ratings)

    - One review per user per place
    - Supports star rating + optional comment
    - Supports visibility_state to allow partner/admin hiding
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    place = models.ForeignKey(
        'places.Place',
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name=_('التقييم')
    )
    comment = models.TextField(blank=True, verbose_name=_('نص التقييم'))

    # Visibility & Moderation
    visibility_state = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='visible'
    )
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hidden_reviews'
    )
    hidden_reason = models.TextField(blank=True, null=True)
    moderation_flags = models.JSONField(default=dict, blank=True)

    # Editing
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'interactions'
        unique_together = ('user', 'place')
        ordering = ['-created_at']
        verbose_name = _('تقييم')
        verbose_name_plural = _('تقييمات')
        indexes = [
            models.Index(fields=['place', 'created_at']),
            models.Index(fields=['place', 'visibility_state', 'created_at']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.rating}★ by {self.user} on {self.place}"

    @property
    def is_visible(self) -> bool:
        return self.visibility_state == 'visible'

    @property
    def is_hidden(self) -> bool:
        # Backward compatible convenience
        return not self.is_visible


class PlaceComment(TimeStampedModel):
    """نموذج التعليقات (Comments)

    Supports:
    - Threaded replies
    - Visibility states (Partner/Admin hidden)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='place_comments'
    )
    place = models.ForeignKey(
        'places.Place',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    content = models.TextField(verbose_name=_('نص التعليق'))
    image = models.ImageField(upload_to='comments/images/', blank=True, null=True, verbose_name=_('صورة'))

    # Visibility & Moderation
    visibility_state = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='visible'
    )
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hidden_comments'
    )
    hidden_reason = models.TextField(blank=True, null=True)
    moderation_flags = models.JSONField(default=dict, blank=True)

    # Editing
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'interactions'
        ordering = ['created_at']
        verbose_name = _('تعليق')
        verbose_name_plural = _('تعليقات')
        indexes = [
            models.Index(fields=['place', 'created_at']),
            models.Index(fields=['place', 'visibility_state', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.user} on {self.place}"

    @property
    def is_visible(self) -> bool:
        return self.visibility_state == 'visible'

    @property
    def is_hidden(self) -> bool:
        # Backward compatible convenience
        return not self.is_visible

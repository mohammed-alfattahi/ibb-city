"""
Special Offers Model
نموذج العروض الخاصة والخصومات
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .establishments import Establishment
from ibb_guide.base_models import TimeStampedModel

class SpecialOffer(TimeStampedModel):
    """
    Represents a time-limited special offer or discount.
    Managed by the partner.
    """
    establishment = models.ForeignKey(
        Establishment, 
        on_delete=models.CASCADE, 
        related_name='special_offers',
        verbose_name=_('المنشأة')
    )
    title = models.CharField(max_length=200, verbose_name=_('عنوان العرض'))
    description = models.TextField(blank=True, verbose_name=_('تفاصيل العرض'))
    
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('السعر القديم'))
    new_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('سعر العرض'))
    
    image = models.ImageField(upload_to='offers/', blank=True, null=True, verbose_name=_('صورة العرض'))
    
    start_date = models.DateTimeField(verbose_name=_('بداية العرض'))
    end_date = models.DateTimeField(verbose_name=_('نهاية العرض'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('نشط'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('عرض خاص')
        verbose_name_plural = _('عروض خاصة')

    def __str__(self):
        return f"{self.title} - {self.establishment.name}"

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > 0:
            discount = ((self.old_price - self.new_price) / self.old_price) * 100
            return int(discount)
        return 0

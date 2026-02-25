from django.db import models
from .advertisements import Advertisement

class AdDailyStats(models.Model):
    """
    Track daily analytics (clicks/views) for an advertisement.
    Used for generating time-series charts.
    """
    advertisement = models.ForeignKey(
        Advertisement, 
        on_delete=models.CASCADE, 
        related_name='daily_stats'
    )
    date = models.DateField(db_index=True)
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('advertisement', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['advertisement', 'date']),
        ]
        verbose_name = 'إحصائيات الإعلان اليومية'
        verbose_name_plural = 'إحصائيات الإعلانات اليومية'

    def __str__(self):
        return f"{self.advertisement} - {self.date}: {self.clicks}/{self.views}"

from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import Place

class PlaceDailyView(models.Model):
    """
    Track daily views for a place to generate analytics charts.
    """
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='daily_views')
    date = models.DateField(db_index=True)
    views = models.PositiveIntegerField(default=0)
    contact_clicks = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('place', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['place', 'date']),
        ]

    def __str__(self):
        return f"{self.place.name} - {self.date}: {self.views}"

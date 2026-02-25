"""
Favorites & Itinerary Models
نماذج المفضلة وجدول الرحلات
"""
from django.db import models
from django.conf import settings
from ibb_guide.base_models import TimeStampedModel


class Favorite(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    place = models.ForeignKey('places.Place', on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        app_label = 'interactions'
        unique_together = ('user', 'place')
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['place']),
        ]

    def __str__(self):
        return f"{self.user} favorited {self.place}"


class Itinerary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='itineraries')
    title = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(default=1)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'interactions'
    
    def __str__(self):
        return f"{self.title} by {self.user}"


class ItineraryItem(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='items')
    place = models.ForeignKey('places.Place', on_delete=models.CASCADE)
    day_number = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    estimated_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    route_risk = models.CharField(max_length=20, default='LOW')

    class Meta:
        app_label = 'interactions'
        ordering = ['day_number', 'order']
        unique_together = ['itinerary', 'day_number', 'order']

    def __str__(self):
        return f"Day {self.day_number} - {self.order}: {self.place}"

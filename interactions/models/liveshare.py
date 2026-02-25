from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string
import uuid

class LiveShareSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='live_shares')
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        app_label = 'interactions'

    def __str__(self):
        return f"LiveShare {self.token[:8]} (User: {self.user.username})"

class LiveLocationPing(models.Model):
    session = models.ForeignKey(LiveShareSession, on_delete=models.CASCADE, related_name='pings')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'interactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ping {self.latitude},{self.longitude} @ {self.created_at}"

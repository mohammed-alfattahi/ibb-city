from django.db import models
from django.conf import settings

class EventLog(models.Model):
    ACTIONS = [
        ("view", "view"),
        ("click", "click"),
        ("save", "save"),
        ("share", "share"),
        ("rate", "rate"),
        ("search", "search"),
        ("open_map", "open_map"),
        ("call", "call"),
        ("book", "book"),
        ("report", "report"),
        ("dwell", "dwell"),
        ("scroll", "scroll"),
        ("nearby_click", "nearby_click"),
    ]




    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                             on_delete=models.SET_NULL)
    # Place is nullable to allow logging generic actions like "search" where no specific place is selected yet
    place = models.ForeignKey("places.Place", on_delete=models.CASCADE, null=True, blank=True)
    
    action = models.CharField(max_length=20, choices=ACTIONS)
    action_value = models.FloatField(null=True, blank=True)
    query_text = models.TextField(null=True, blank=True)
    
    device = models.CharField(max_length=120, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["place", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} on {self.created_at}"

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PlacesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'places'
    verbose_name = 'الوجهات والمعالم السياحية'
    
    def ready(self):
        # Activate aggregate signals for auto-updating ratings/counts
        from .services import aggregate_signals  # noqa: F401

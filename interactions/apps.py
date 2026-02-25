from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class InteractionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interactions'
    verbose_name = 'التفاعل المجتمعي والتقييمات'

    def ready(self):
        import interactions.signals

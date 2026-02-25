from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class ManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'management'
    verbose_name = 'إدارة المحتوى والعمليات'

    def ready(self):
        import management.services.moderation_signals

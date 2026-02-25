from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
# اعدادات داخل django لتطبيق المستخدمين والحسابات
class UsersConfig(AppConfig):
    # اعدادات داخل django لتطبيق المستخدمين والحسابات
    default_auto_field = 'django.db.models.BigAutoField'
    # اسم التطبيق
    name = 'users'
    # اسم التطبيق باللغة العربية
    verbose_name = 'إدارة المستخدمين والحسابات'

    def ready(self):
        import users.signals

from django.core.cache import cache
from management.models import SystemSetting

class SettingsService:
    CACHE_KEY_PREFIX = 'system_setting_'
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

    @classmethod
    def get(cls, key, default=None):
        """
        Get a setting value by key, checking cache first.
        """
        cache_key = f"{cls.CACHE_KEY_PREFIX}{key}"
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        try:
            setting = SystemSetting.objects.get(key=key)
            value = cls._cast_value(setting.value, setting.data_type)
            cache.set(cache_key, value, cls.CACHE_TIMEOUT)
            return value
        except SystemSetting.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value, data_type='string', description=''):
        """
        Set a setting value and update cache.
        """
        setting, created = SystemSetting.objects.update_or_create(
            key=key,
            defaults={
                'value': str(value),
                'data_type': data_type,
                'description': description
            }
        )
        
        # Update cache
        cache_key = f"{cls.CACHE_KEY_PREFIX}{key}"
        cache.set(cache_key, value, cls.CACHE_TIMEOUT)
        
        # Invalidate global public settings cache
        cache.delete("system_settings:public")
        return setting

    @classmethod
    def get_all_public(cls):
        """
        Get all public settings as a dictionary. Cached for 1 hour.
        """
        cache_key = "system_settings:public"
        cached_settings = cache.get(cache_key)
        if cached_settings is not None:
            return cached_settings

        settings_qs = SystemSetting.objects.filter(is_public=True)
        public_settings = {s.key: cls._cast_value(s.value, s.data_type) for s in settings_qs}
        
        cache.set(cache_key, public_settings, 3600)
        return public_settings

    @staticmethod
    def _cast_value(value, data_type):
        if data_type == 'integer':
            return int(value)
        elif data_type == 'boolean':
            return value.lower() in ('true', '1', 't', 'yes')
        return value

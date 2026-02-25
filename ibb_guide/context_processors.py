from management.services.settings_service import SettingsService
from django.core.cache import cache

def system_settings(request):
    """
    Inject public system settings into the template context.
    """
    try:
        return {
            'system_settings': SettingsService.get_all_public()
        }
    except Exception:
        # Avoid crashing if DB is not ready or other errors
        return {'system_settings': {}}

def notifications(request):
    """
    Inject unread notification count for the user.
    Uses request-level reuse and short TTL (60s) caching.
    """
    if request.user.is_authenticated:
        # 1. Reuse computed value if already present in this request
        if hasattr(request, '_unread_notifications_count'):
            return {'unread_notifications_count': request._unread_notifications_count}

        # 2. Check Cache
        cache_key = f"notif_ctx:{request.user.id}"
        count = cache.get(cache_key)
        
        if count is None:
            from interactions.models import Notification
            count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            # Cache for a short time to balance freshness and performance
            cache.set(cache_key, count, 60)
        
        # 3. Store on request for reuse in same cycle
        request._unread_notifications_count = count
        return {'unread_notifications_count': count}
    return {}

def favorites(request):
    """
    Inject favorite count for the user.
    TTL 60 seconds to reduce recurrent DB counts on dashboard/profile views.
    """
    if request.user.is_authenticated:
        # 1. Reuse computed value if already present in this request
        if hasattr(request, '_favorites_count'):
            return {'favorites_count': request._favorites_count}

        # 2. Check Cache
        cache_key = f"fav_count:{request.user.id}"
        count = cache.get(cache_key)
        
        if count is None:
            from interactions.models import Favorite
            count = Favorite.objects.filter(user=request.user).count()
            cache.set(cache_key, count, 60)
            
        # 3. Store on request for reuse in same cycle
        request._favorites_count = count
        return {'favorites_count': count}
    return {}

def onesignal(request):
    """
    Provide OneSignal App ID without hitting the database.
    """
    from django.conf import settings
    return {'onesignal_app_id': getattr(settings, 'ONESIGNAL_APP_ID', '')}

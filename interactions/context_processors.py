from .models import Notification
from django.conf import settings
from django.core.cache import cache

def notification_context(request):
    if request.user.is_authenticated:
        cache_key = f"notif_ctx:{request.user.id}:{1 if request.user.is_staff else 0}"
        cached = cache.get(cache_key)
        if cached:
            request._unread_notifications_count = cached.get('unread_notifications_count', 0)
            return cached

        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        request._unread_notifications_count = unread_count
        # Fetch last 5 notifications for the dropdown (limit fields)
        latest_notifications = list(
            Notification.objects.filter(recipient=request.user)
            .only(
                'id', 'title', 'message', 'notification_type', 'event_type',
                'metadata', 'created_at', 'is_read', 'action_url'
            )
            .order_by('-created_at')[:5]
        )
        
        context = {
            'unread_notifications_count': unread_count,
            'latest_notifications': latest_notifications,
            'onesignal_app_id': getattr(settings, 'ONESIGNAL_APP_ID', ''),
        }
        
        # Add pending changes count for staff users (admin sidebar badge)
        if request.user.is_staff:
            from management.models import PendingChange
            from places.models import Establishment
            from users.models import PartnerProfile
            context['pending_changes_count'] = PendingChange.objects.filter(status='pending').count()
            context['pending_establishments_count'] = Establishment.objects.filter(approval_status='pending').count()
            context['pending_partners_count'] = PartnerProfile.objects.filter(status='pending').count()
        
        cache.set(cache_key, context, 30)
        return context
    return {
        'unread_notifications_count': 0,
        'latest_notifications': [],
    }

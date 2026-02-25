import traceback
import sys
from urllib.parse import urlparse

from django.conf import settings
from django.http import Http404
from django.http.response import HttpResponseRedirectBase
from django.shortcuts import resolve_url
from django.utils.deprecation import MiddlewareMixin

from management.models import ErrorLog
from interactions.onesignal_service import send_onesignal_notification
from django.contrib.auth import get_user_model
from ibb_guide.utils.htmx import is_htmx, htmx_redirect

class SystemMonitorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        # Ignore 404s (Not a crash)
        if isinstance(exception, Http404):
            return None
            
        # Capture unhandled exceptions
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Log to DB
        user = request.user if request.user.is_authenticated else None
        ErrorLog.objects.create(
            path=request.path,
            method=request.method,
            error_message=str(exception),
            traceback=tb_str,
            user=user
        )
        
        # Send Alert to Superusers (Alerts on Crash)
        try:
            from management.services.notification_service import NotificationService
            NotificationService.notify_admins(
                title="⚠️ System Crash Alert",
                message=f"Error at {request.path}: {str(exception)[:100]}",
                notification_type='error'
            )
        except Exception as e:
            # Fallback if notification fails, print to stderr
            print(f"Failed to send alert: {e}", file=sys.stderr)
            
        return None # Let Django handle the 500 response


class HTMXRedirectMiddleware(MiddlewareMixin):
    """
    Convert login redirects into HX-Redirect for HTMX requests.
    This avoids injecting the login page inside a partial target.
    """

    def process_response(self, request, response):
        if not is_htmx(request):
            return response

        if not isinstance(response, HttpResponseRedirectBase):
            return response

        location = response.get('Location')
        if not location:
            return response

        login_url = resolve_url(settings.LOGIN_URL)
        location_path = urlparse(location).path or ''
        if location_path == login_url:
            return htmx_redirect(location)

        return response

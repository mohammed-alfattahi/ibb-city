
import requests
import json
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def send_onesignal_notification(title, message, user_emails=None, user_ids=None):
    """
    Send Push Notification via OneSignal.
    
    Args:
        title (str): Notification Title.
        message (str): Notification Body.
        user_ids (list): List of user IDs (OneSignal Player IDs or External IDs) to send to.
                        Using 'include_external_user_ids' matches our Django User IDs if we set them on frontend.
                        If None, sends to All Subscribed Users.
    """
    
    if not hasattr(settings, 'ONESIGNAL_APP_ID') or not hasattr(settings, 'ONESIGNAL_API_KEY'):
        logger.warning("OneSignal credentials not found in settings.")
        return

    header = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}"
    }

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "headings": {"en": title, "ar": title},
        "contents": {"en": message, "ar": message},
    }

    # Targeting
    if user_ids:
        # Assuming we will identify users by their Django ID via setExternalUserId in JS
        payload["include_external_user_ids"] = [str(uid) for uid in user_ids]
    else:
        # Broadcast to all
        payload["included_segments"] = ["All"]

    try:
        req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
        logger.info(f"OneSignal Response: {req.status_code}")
        return req.json()
    except Exception as e:
        logger.error(f"Error sending OneSignal notification: {e}", exc_info=True)
        return None


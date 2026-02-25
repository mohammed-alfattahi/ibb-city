"""
Firebase Cloud Messaging Service for sending push notifications.
Uses Firebase Admin SDK for server-side notification delivery.
"""
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings


# Initialize Firebase Admin SDK
_firebase_app = None

def _get_firebase_app():
    """Get or initialize Firebase Admin SDK app."""
    global _firebase_app
    if _firebase_app is None:
        try:
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if cred_path:
                cred = credentials.Certificate(str(cred_path))
                _firebase_app = firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully")
            else:
                print("FIREBASE_CREDENTIALS_PATH not set in settings")
        except ValueError:
            # App already exists
            _firebase_app = firebase_admin.get_app()
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {e}")
    return _firebase_app


def send_fcm_notification(title, message, fcm_token, data=None, action_url=None):
    """
    Send Push Notification via Firebase Cloud Messaging.
    
    Args:
        title (str): Notification Title.
        message (str): Notification Body.
        fcm_token (str): Single FCM token to send to.
        data (dict): Additional data to send with the notification.
        action_url (str): URL to open when notification is clicked.
    
    Returns:
        str: Message ID if successful, None otherwise.
    """
    app = _get_firebase_app()
    if not app:
        print("Firebase not initialized, cannot send notification")
        return None
    
    try:
        # Build notification
        notification = messaging.Notification(
            title=title,
            body=message
        )
        
        # Build data payload
        notification_data = data or {}
        if action_url:
            notification_data['action_url'] = action_url
        
        # Build message
        fcm_message = messaging.Message(
            notification=notification,
            data=notification_data,
            token=fcm_token,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=message,
                    icon='/static/icons/notification-icon.png'
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=action_url or '/'
                )
            )
        )
        
        # Send message
        response = messaging.send(fcm_message)
        print(f"FCM Notification sent successfully: {response}")
        return response
    except Exception as e:
        print(f"Error sending FCM notification: {e}")
        return None


def send_fcm_notification_to_multiple(title, message, fcm_tokens, data=None):
    """
    Send Push Notification to multiple FCM tokens.
    
    Args:
        title (str): Notification Title.
        message (str): Notification Body.
        fcm_tokens (list): List of FCM tokens to send to.
        data (dict): Additional data to send with the notification.
    
    Returns:
        messaging.BatchResponse: Response from Firebase.
    """
    app = _get_firebase_app()
    if not app:
        print("Firebase not initialized, cannot send notification")
        return None
    
    if not fcm_tokens:
        print("No FCM tokens provided")
        return None
    
    try:
        # Build notification
        notification = messaging.Notification(
            title=title,
            body=message
        )
        
        # Build message for multiple recipients
        multicast_message = messaging.MulticastMessage(
            notification=notification,
            data=data or {},
            tokens=fcm_tokens
        )
        
        # Send message
        response = messaging.send_each_for_multicast(multicast_message)
        print(f"FCM Multicast: {response.success_count} sent, {response.failure_count} failed")
        return response
    except Exception as e:
        print(f"Error sending FCM multicast notification: {e}")
        return None

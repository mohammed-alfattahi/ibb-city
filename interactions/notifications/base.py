"""
Base Notification Service
الوحدة الأساسية لإنشاء الإشعارات
"""
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from interactions.models import Notification, NotificationPreference

User = get_user_model()


class NotificationBase:
    """الفئة الأساسية لإنشاء الإشعارات"""
    
    @staticmethod
    def _create_notification(recipient, notification_type, title, message, related_object=None, action_url=''):
        """
        دالة مساعدة لإنشاء إشعار مع التحقق من تفضيلات المستخدم
        
        Returns: Notification object if created, None if preferences blocked it
        """
        # Check user preferences before creating notification
        try:
            prefs = NotificationPreference.get_or_create_for_user(recipient)
            if not prefs.is_notification_enabled(notification_type):
                # User has disabled this notification type
                return None
        except Exception:
            # If preferences check fails, proceed with notification (fail-open)
            pass
        
        notification_data = {
            'recipient': recipient,
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'action_url': action_url,
        }
        
        if related_object:
            notification_data['content_type'] = ContentType.objects.get_for_model(related_object)
            notification_data['object_id'] = related_object.pk
        
        return Notification.objects.create(**notification_data)

    @staticmethod
    def get_unread_count(user):
        """الحصول على عدد الإشعارات غير المقروءة"""
        return Notification.objects.filter(recipient=user, is_read=False).count()
    
    @staticmethod
    def mark_all_as_read(user):
        """تعليم جميع إشعارات المستخدم كمقروءة"""
        from django.utils import timezone
        return Notification.objects.filter(
            recipient=user, 
            is_read=False
        ).update(
            is_read=True, 
            read_at=timezone.now()
        )

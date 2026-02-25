"""
Notifications Package
وحدة الإشعارات المقسمة

الهيكل:
- notification_service.py: النظام Event-Driven (OneSignal)
- base.py: الفئة الأساسية
- partner.py: إشعارات الشركاء
- admin.py: إشعارات الإدارة
- tourist.py: إشعارات السياح
"""
# Event-Driven Service (for signals integration)
from .notification_service import NotificationService as EventNotificationService

# New Modular Notifications
from .base import NotificationBase
from .partner import PartnerNotifications
from .admin import AdminNotifications
from .tourist import TouristNotifications


class NotificationService(PartnerNotifications, AdminNotifications, TouristNotifications):
    """
    خدمة الإشعارات المركزية الموحدة
    
    ترث من جميع فئات الإشعارات المباشرة + تدعم Event-Driven.
    """
    # Delegate to Event-Driven service for signals
    emit_event = staticmethod(EventNotificationService.emit_event)
    notify_establishment_update_request = staticmethod(EventNotificationService.notify_establishment_update_request)


__all__ = [
    'NotificationService',
    'NotificationBase',
    'PartnerNotifications', 
    'AdminNotifications',
    'TouristNotifications',
    'EventNotificationService',
]

"""
Notification Service - Centralized notification logic.

This service encapsulates all notification-related business logic for:
- Sending approval/rejection notifications
- Weather alerts broadcasting
- Request status change notifications
"""
from django.contrib.auth import get_user_model
from interactions.onesignal_service import send_onesignal_notification

from django.contrib.auth import get_user_model
from interactions.onesignal_service import send_onesignal_notification
from interactions.models.notifications import Notification

User = get_user_model()


class NotificationService:
    """Service for handling all app notifications."""
    
    # Severity translations
    SEVERITY_AR = {
        'YELLOW': 'تحذير أصفر',
        'ORANGE': 'تحذير برتقالي',
        'RED': 'تحذير أحمر',
    }
    
    @staticmethod
    def send_weather_alert(alert) -> bool:
        """
        Broadcast a weather alert to all users.
        
        Args:
            alert: WeatherAlert instance
            
        Returns:
            bool: Success status
        """
        user_ids = list(User.objects.values_list('id', flat=True))
        
        severity_text = NotificationService.SEVERITY_AR.get(alert.severity, 'تنبيه')
        title = f"⚠️ {severity_text} - {alert.title}"
        message = alert.description[:100] + "..." if len(alert.description) > 100 else alert.description
        
        # 1. Create DB Records for all users (Warning: Expensive for large user base, optimize with bulk_create later)
        # For now, we only log a 'general' system notification or iterate
        # Optimization: Just send push for now, or log 1 global record if supported
        
        return send_onesignal_notification(
            title=title,
            message=message,
            user_ids=user_ids
        )
    
    @staticmethod
    def notify_request_approved(request_obj) -> bool:
        """
        Notify a user that their request was approved.
        
        Args:
            request_obj: Request model instance
            
        Returns:
            bool: Success status
        """
        # 1. Create DB Record
        Notification.objects.create(
            recipient=request_obj.user,
            notification_type='pending_change_approved',
            title="تمت الموافقة على طلبك",
            message=f"وافق المشرف على طلب التعديل الخاص بك: {request_obj.description}",
            related_object=request_obj
        )

        # 2. Send Push
        return send_onesignal_notification(
            title="تمت الموافقة على طلبك",
            message=f"وافق المشرف على طلب التعديل الخاص بك: {request_obj.description}",
            user_ids=[request_obj.user.id]
        )
    
    @staticmethod
    def notify_request_rejected(request_obj, reason: str = "") -> bool:
        """
        Notify a user that their request was rejected.
        
        Args:
            request_obj: Request model instance
            reason: Rejection reason
            
        Returns:
            bool: Success status
        """
        # 1. Create DB Record
        Notification.objects.create(
            recipient=request_obj.user,
            notification_type='pending_change_rejected',
            title="رفض الطلب",
            message=f"عذراً، تم رفض طلب التعديل: {reason}",
            related_object=request_obj
        )

        return send_onesignal_notification(
            title="رفض الطلب",
            message=f"عذراً، تم رفض طلب التعديل: {reason}",
            user_ids=[request_obj.user.id]
        )
    
    @staticmethod
    def notify_request_needs_info(request_obj, message: str, deadline: str = None) -> bool:
        """
        Notify a user that additional info is needed for their request.
        
        Args:
            request_obj: Request model instance
            message: Info request message
            deadline: Optional deadline string
            
        Returns:
            bool: Success status
        """
        msg_body = f"يحتاج المشرف إلى مزيد من المعلومات حول طلبك: {message}"
        if deadline:
            msg_body += f" (المهلة: {deadline})"
            
        Notification.objects.create(
            recipient=request_obj.user,
            notification_type='partner_needs_info', # Or generic
            title="مطلوب معلومات إضافية",
            message=msg_body,
            related_object=request_obj
        )

        return send_onesignal_notification(
            title="مطلوب معلومات إضافية",
            message=msg_body,
            user_ids=[request_obj.user.id]
        )
    
    @staticmethod
    def notify_conditional_approval(request_obj, conditions: str, deadline: str = None) -> bool:
        """
        Notify a user of conditional approval.
        
        Args:
            request_obj: Request model instance
            conditions: Approval conditions
            deadline: Optional deadline string
            
        Returns:
            bool: Success status
        """
        msg = f"تمت الموافقة المشروطة على طلبك. الشروط: {conditions}. (المهلة: {deadline or 'غير محددة'})"
        
        Notification.objects.create(
            recipient=request_obj.user,
            notification_type='pending_change_approved', # Close enough
            title="موافقة مشروطة",
            message=msg,
            related_object=request_obj
        )

        return send_onesignal_notification(
            title="موافقة مشروطة",
            message=msg,
            user_ids=[request_obj.user.id]
        )
    
    @staticmethod
    def notify_partner_approved(partner_profile) -> bool:
        """
        Notify a partner that their registration was approved.
        
        Args:
            partner_profile: PartnerProfile instance
            
        Returns:
            bool: Success status
        """
        Notification.objects.create(
            recipient=partner_profile.user,
            notification_type='partner_approved',
            title="تمت الموافقة على حسابك",
            message="تهانينا! تمت الموافقة على حساب الشريك الخاص بك.",
            related_object=partner_profile
        )

        return send_onesignal_notification(
            title="تمت الموافقة على حسابك",
            message="تهانينا! تمت الموافقة على حساب الشريك الخاص بك.",
            user_ids=[partner_profile.user.id]
        )
    
    @staticmethod
    def notify_partner_rejected(user, reason: str = "") -> bool:
        """
        Notify a partner that their registration was rejected.
        
        Args:
            user: User instance
            reason: Rejection reason
            
        Returns:
            bool: Success status
        """
        Notification.objects.create(
            recipient=user,
            notification_type='partner_rejected',
            title="تم رفض طلب الشراكة",
            message=f"عذراً، تم رفض طلب الشراكة الخاص بك. السبب: {reason}",
        )

        return send_onesignal_notification(
            title="تم رفض طلب الشراكة",
            message=f"عذراً، تم رفض طلب الشراكة الخاص بك. السبب: {reason}",
            user_ids=[user.id]
        )

    @staticmethod
    def notify_admins(title: str, message: str, url: str = None, notification_type: str = 'system') -> bool:
        """
        Notify all superusers/admins about an event.
        Persists to DB and sends Push.
        """
        admins = User.objects.filter(is_superuser=True)
        admin_ids = list(admins.values_list('id', flat=True))
        
        if not admin_ids:
            return False
            
        # 1. Bulk Create DB Records
        notifications = [
            Notification(
                recipient=admin,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=url or ''
            ) for admin in admins
        ]
        Notification.objects.bulk_create(notifications)
        
        # 2. Send Push
        return send_onesignal_notification(
            title=title,
            message=message,
            user_ids=admin_ids
        )

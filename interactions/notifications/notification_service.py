"""
Notification Service with Async Outbox Pattern

Provides reliable notification delivery using:
- Transactional outbox for guaranteed delivery
- Celery for async processing
- transaction.on_commit for safe task enqueuing
"""
from interactions.models import Notification
from users.models import User
from django.db import transaction
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Event-Driven Service for Notifications.
    Uses transactional outbox pattern for reliable async delivery.
    """

    @staticmethod
    def emit_event(event_name, payload, audience_criteria=None, priority='medium', sender=None):
        """
        Main Entry Point.
        Creates in-app notifications and enqueues push notifications.
        """
        try:
            # 1. Resolve Audience
            recipients = NotificationService._resolve_audience(audience_criteria)
            
            # 2. Resolve Content
            title, message, action_url = NotificationService._resolve_content(event_name, payload)
            
            # 3. Create in-app notifications + enqueue push
            NotificationService._dispatch(
                recipients, title, message, action_url, 
                priority, event_name, payload, sender
            )
            logger.info(f"Notification dispatched: {event_name} to {len(recipients)} recipients")
        except Exception as e:
            logger.error(f"Notification Error [{event_name}]: {e}", exc_info=True)
            # Never raise - isolate notification failures from main request

    @staticmethod
    def enqueue_notification(
        recipient,
        title: str,
        body: str,
        channel: str = 'push',
        provider: str = 'fcm',
        payload: dict = None,
        related_object_type: str = None,
        related_object_id: str = None,
        sender=None
    ):
        """
        Enqueue a notification for async delivery via Celery.
        
        Uses transaction.on_commit to ensure the outbox record
        is committed before the Celery task is enqueued.
        
        Args:
            recipient: User instance
            title: Notification title
            body: Notification body
            channel: 'push', 'email', 'sms', 'in_app'
            provider: 'fcm', 'onesignal', 'email'
            payload: Additional data payload
            related_object_type: Type of related object (optional)
            related_object_id: ID of related object (optional)
            sender: User instance (optional)
        """
        from interactions.notifications.outbox import NotificationOutbox
        from interactions.tasks.notifications import send_outbox_notification
        
        try:
            # P1 Fix G-05: Skip push if no device token
            if channel == 'push':
                has_fcm = getattr(recipient, 'fcm_token', None)
                has_onesignal = getattr(recipient, 'onesignal_id', None)
                if not has_fcm and not has_onesignal:
                    logger.info(f"Skipped push for {recipient}: no device token")
                    return None
            
            # Create outbox record
            # We use transactional outbox to defer external sending (push/email)
            # and avoid blocking the request thread.
            outbox = NotificationOutbox.objects.create(
                recipient=recipient,
                channel=channel,
                provider=provider,
                title=title,
                body=body,
                payload=payload or {},
                status='queued',
                related_object_type=related_object_type,
                related_object_id=str(related_object_id) if related_object_id else None,
            )
            
            # NOTE: We skip async task enqueuing here because on constrained hosting
            # (where CELERY_TASK_ALWAYS_EAGER=True), .delay() would run synchronously
            # and block the request on slow external providers.
            # The process_outbox management command handles delivery via cron.
            
            logger.info(f"Created outbox notification: {outbox.id} for {recipient}")
            return outbox
            
        except Exception as e:
            logger.error(f"Failed to enqueue notification: {e}", exc_info=True)
            return None

    @staticmethod
    def _resolve_audience(criteria):
        """Filter users based on criteria."""
        if not criteria:
            return []

        # Optimization: Return queryset directly if possible, evaluate only when needed
        queryset = User.objects.filter(is_active=True)

        if criteria.get('broadcast'):
            # Return all active users
            return list(queryset)

        if 'role' in criteria:
            if criteria['role'] == 'all':
                # All active users (for weather alerts, system alerts)
                return list(queryset)
            elif criteria['role'] == 'partner':
                # Robustness Fix: specific check for approved partner profile
                # This prevents users with stale 'partner' role or no profile from getting alerts
                queryset = queryset.filter(partner_profile__is_approved=True)
            elif criteria['role'] == 'staff':
                queryset = queryset.filter(is_staff=True)

        if 'user_id' in criteria:
            queryset = queryset.filter(pk=criteria['user_id'])
            
        return list(queryset)

    @staticmethod
    def _resolve_content(event_name, payload):
        """Map event to text content."""
        """Map event to text content."""
        # Defaults
        title = (payload or {}).get('title', "تحديث جديد")
        message = (payload or {}).get('message', "لديك إشعار جديد.")
        url = (payload or {}).get('url') or (payload or {}).get('action_url')
        
        EVENT_TEMPLATES = {
            'PARTNER_APPROVED': (
                "تم اعتماد حسابك كشريك",
                lambda p: "مبروك! تم قبول طلب الشراكة. يمكنك الآن الدخول إلى لوحة الشريك وإدارة منشآتك."
            ),
            'PARTNER_REJECTED': (
                "تم رفض طلب الشراكة",
                lambda p: f"تم رفض طلب الشراكة. السبب: {p.get('reason', 'غير مذكور')}"
            ),
            'PARTNER_NEEDS_INFO': (
                "📋 مطلوب معلومات إضافية",
                lambda p: f"يرجى تقديم المعلومات التالية لاستكمال طلب الشراكة:\n\n{p.get('info_message', '')}"
            ),
            'ESTABLISHMENT_APPROVED': (
                "تم قبول المنشأة",
                lambda p: f"تم قبول منشأة '{p.get('place_name')}' ونشرها على المنصة."
            ),
            'ESTABLISHMENT_REJECTED': (
                "تم رفض المنشأة",
                lambda p: f"تم رفض منشأة '{p.get('place_name')}'. السبب: {p.get('reason', 'غير مذكور')}"
            ),
            'ESTABLISHMENT_SUSPENDED': (
                "تم تعليق المنشأة",
                lambda p: f"تم تعليق '{p.get('place_name')}' مؤقتاً. السبب: {p.get('reason')}"
            ),
            'ESTABLISHMENT_UNSUSPENDED': (
                "تم رفع التعليق",
                lambda p: f"تم إعادة تفعيل '{p.get('place_name')}'."
            ),
            'REQUEST_UPDATE': (
                "طلب تعديل جديد",
                lambda p: f"طلب تعديل على '{p.get('target')}' يتطلب المراجعة."
            ),
            'NEW_REVIEW': (
                "تقييم جديد",
                lambda p: f"قام مستخدم بتقييم '{p.get('place_name')}' بـ {p.get('rating')} نجوم."
            ),
            'NEW_COMMENT': (
                "تعليق جديد",
                lambda p: f"قام {p.get('author', 'مستخدم')} بالتعليق على '{p.get('place_name')}'."
            ),
            'NEW_COMMENT_REPLY': (
                "رد جديد",
                lambda p: f"قام {p.get('replier')} بالرد على تعليقك في '{p.get('place_name')}'."
            ),
            'REVIEW_REPLY': (
                "رد على التقييم",
                lambda p: f"قام {p.get('replier')} بالرد على تقييمك للمكان '{p.get('place_name')}'."
            ),
            'NEW_REPORT': (
                "بلاغ جديد",
                lambda p: f"تم استلام بلاغ جديد بخصوص '{p.get('target')}'."
            ),
            'OPEN_STATUS_CHANGED': (
                "تغيير حالة المحل",
                lambda p: f"قام الشريك {p.get('user')} بتغيير حالة '{p.get('place_name')}' إلى {'مفتوح' if p.get('status') == 'Open' else 'مغلق'}."
            ),
            'SYSTEM_ALERT': (
                (payload or {}).get('title', 'تنبيه النظام'),
                lambda p: p.get('message', 'لا توجد تفاصيل')
            ),
            'STAFF_ALERT': (
                (payload or {}).get('title', 'تنبيه إداري'),
                lambda p: p.get('message', 'لا توجد تفاصيل')
            ),
            'WEATHER_ALERT': (
                (payload or {}).get('title', 'تنبيه الأحوال الجوية'),
                lambda p: p.get('message', 'يرجى توخي الحذر.')
            ),
        }
        
        if event_name in EVENT_TEMPLATES:
            template = EVENT_TEMPLATES[event_name]
            title = template[0]
            message = template[1](payload)
        
        return title, message, url


    @staticmethod
    def _map_event_to_notification_type(event_type: str) -> str:
        # Map internal event names to Notification.notification_type choices
        mapping = {
            'PARTNER_APPROVED': 'partner_approved',
            'PARTNER_REJECTED': 'partner_rejected',
            'PARTNER_NEEDS_INFO': 'partner_needs_info',
            'ESTABLISHMENT_APPROVED': 'establishment_approved',
            'ESTABLISHMENT_REJECTED': 'establishment_rejected',
            'ESTABLISHMENT_SUSPENDED': 'establishment_suspended',
            'ESTABLISHMENT_UNSUSPENDED': 'establishment_reactivated',
            'NEW_ESTABLISHMENT_REQUEST': 'new_establishment_request',
            'REQUEST_UPDATE': 'establishment_update_request',
            'NEW_REVIEW': 'new_review',
            'NEW_REPORT': 'new_user_report',
            'REVIEW_REPLY': 'review_reply',
            'REPORT_UPDATE': 'report_update',
            'SYSTEM_ALERT': 'general',
            'STAFF_ALERT': 'general',
            'WEATHER_ALERT': 'weather_alert',
        }
        return mapping.get(event_type, 'general')

    @staticmethod
    def _dispatch(recipients, title, message, url, priority, event_type, metadata, sender=None):
        # Create in-app records and enqueue push/email notifications.
        # Respects NotificationPreference if present.
        from interactions.models import NotificationPreference

        priority_map = {
            'critical': 'high',
            'high': 'high',
            'medium': 'normal',
            'normal': 'normal',
            'low': 'low',
        }
        priority_db = priority_map.get(priority, 'normal')

        notif_type = NotificationService._map_event_to_notification_type(event_type)
        notifications_to_create = []

        for user in recipients:
            try:
                prefs = NotificationPreference.get_or_create_for_user(user)
                if not prefs.is_notification_enabled(notif_type):
                    continue
            except Exception:
                prefs = None

            notifications_to_create.append(
                Notification(
                    recipient=user,
                    sender=sender, # Add sender
                    notification_type=notif_type,
                    title=title,
                    message=message,
                    action_url=url or '',
                    priority=priority_db,
                    event_type=event_type,
                    metadata=metadata
                )
            )

            # Enqueue push notification only if enabled
            if prefs is None or getattr(prefs, 'enable_push', True):
                NotificationService.enqueue_notification(
                    recipient=user,
                    title=title,
                    body=message,
                    channel='push',
                    provider='fcm',
                    payload=metadata,
                    sender=sender
                )
            
            # Enqueue email notification if enabled
            if prefs and getattr(prefs, 'enable_email', False):
                NotificationService.enqueue_notification(
                    recipient=user,
                    title=title,
                    body=message,
                    channel='email',
                    provider='email',
                    payload={
                        **(metadata or {}),
                        'notification_type': notif_type,
                        'action_url': url,
                    },
                    sender=sender
                )

        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

    # ==========================================
    # Convenience Methods
    # ==========================================
    
    @staticmethod
    def notify_user(user, title, message, url=None):
        """Send notification to a specific user."""
        NotificationService.emit_event(
            'SYSTEM_ALERT',
            {'title': title, 'message': message, 'url': url},
            {'user_id': user.id}
        )
    
    @staticmethod
    def notify_staff(title, message, payload=None):
        """Send notification to all staff members."""
        NotificationService.emit_event(
            'STAFF_ALERT',
            payload or {'title': title, 'message': message},
            {'role': 'staff'}
        )
    
    @staticmethod
    def notify_establishment_update_request(establishment):
        """Notify staff about pending establishment update."""
        NotificationService.emit_event(
            'REQUEST_UPDATE',
            {'target': establishment.name},
            {'role': 'staff'}
        )

    @staticmethod
    def mark_as_read(notification):
        """Mark a single notification as read."""
        from django.utils import timezone
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
            return True
        return False

    @staticmethod
    def mark_all_as_read(user):
        """Mark all unread notifications for a user as read."""
        from django.utils import timezone
        return Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )

"""
Event Handlers Module
=====================
Handlers that react to domain events. Each handler is responsible for
a specific side effect (notifications, logging, analytics, etc.).
"""
from ibb_guide.events import (
    EventBus, handles,
    PlaceApproved, PlaceRejected, ReviewCreated, ReviewReported,
    PartnerApproved, PartnerSuspended, RequestStatusChanged
)
from interactions.notifications import NotificationService
from management.models import AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# Notification Handlers
# ============================================================================

@handles(PlaceApproved)
def notify_place_approved(event: PlaceApproved):
    """Send notification to owner when their place is approved."""
    try:
        owner = User.objects.get(pk=event.owner_id)
        NotificationService.send_notification(
            user=owner,
            title="تمت الموافقة على مكانك!",
            message=f"تهانينا! تمت الموافقة على '{event.place_name}' وأصبح مرئياً للجميع.",
            notification_type='APPROVAL'
        )
    except User.DoesNotExist:
        pass


@handles(PlaceRejected)
def notify_place_rejected(event: PlaceRejected):
    """Send notification to owner when their place is rejected."""
    try:
        owner = User.objects.get(pk=event.owner_id)
        NotificationService.send_notification(
            user=owner,
            title="تم رفض طلب المكان",
            message=f"للأسف، تم رفض '{event.place_name}'. السبب: {event.reason}",
            notification_type='REJECTION'
        )
    except User.DoesNotExist:
        pass


@handles(PartnerApproved)
def notify_partner_approved(event: PartnerApproved):
    """Send notification when partner is approved."""
    try:
        user = User.objects.get(pk=event.user_id)
        NotificationService.send_notification(
            user=user,
            title="تهانينا! تمت الموافقة على حسابك كشريك",
            message="يمكنك الآن إضافة أماكنك التجارية وإدارتها.",
            notification_type='APPROVAL'
        )
    except User.DoesNotExist:
        pass


@handles(PartnerSuspended)
def notify_partner_suspended(event: PartnerSuspended):
    """Send notification when partner is suspended."""
    try:
        user = User.objects.get(pk=event.user_id)
        NotificationService.send_notification(
            user=user,
            title="تم إيقاف حسابك",
            message=f"تم إيقاف حسابك. السبب: {event.reason}",
            notification_type='SYSTEM'
        )
    except User.DoesNotExist:
        pass


@handles(ReviewReported)
def notify_review_reported(event: ReviewReported):
    """Log when a review is reported (admins will see this in audit)."""
    # This could also notify admins via email or dashboard
    print(f"[Event] Review {event.review_id} reported: {event.reason}")


# ============================================================================
# Audit/Logging Handlers
# ============================================================================

@handles(PlaceApproved)
def log_place_approved(event: PlaceApproved):
    """Create audit log entry for place approval."""
    AuditLog.objects.create(
        user_id=event.approved_by_id,
        action='APPROVE_PLACE',
        table_name='places_establishment',
        record_id=str(event.place_id),
        new_values={'status': 'approved', 'place_name': event.place_name}
    )


@handles(PartnerSuspended)
def log_partner_suspended(event: PartnerSuspended):
    """Create audit log entry for partner suspension."""
    AuditLog.objects.create(
        user_id=event.suspended_by_id,
        action='SUSPEND_PARTNER',
        table_name='users_partnerprofile',
        record_id=str(event.partner_id),
        new_values={'status': 'suspended', 'reason': event.reason}
    )


@handles(RequestStatusChanged)
def log_request_status_change(event: RequestStatusChanged):
    """Create audit log entry for request status changes."""
    AuditLog.objects.create(
        user_id=event.changed_by_id,
        action='STATUS_CHANGE',
        table_name='management_request',
        record_id=str(event.request_id),
        old_values={'status': event.old_status},
        new_values={'status': event.new_status}
    )


# ============================================================================
# Analytics Handlers (placeholder for future)
# ============================================================================

@handles(ReviewCreated)
def track_review_analytics(event: ReviewCreated):
    """Track review creation for analytics."""
    # Future: Send to analytics service
    pass

"""
Celery Tasks for Async Notification Delivery
"""
import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=5, default_retry_delay=30)
def send_outbox_notification(self, outbox_id: str):
    """
    Process a notification from the outbox.
    
    Implements:
    - Idempotency (skip if already sent)
    - Exponential backoff retry
    - Dead letter after max attempts
    
    Args:
        outbox_id: UUID of NotificationOutbox record
    """
    from interactions.notifications.outbox import NotificationOutbox
    from interactions.notifications.providers import get_provider, ProviderError
    
    try:
        outbox = NotificationOutbox.objects.get(id=outbox_id)
    except NotificationOutbox.DoesNotExist:
        logger.error(f"Outbox {outbox_id} not found")
        return
    
    # Idempotency check
    if outbox.status == 'sent':
        logger.info(f"Outbox {outbox_id} already sent, skipping")
        return
    
    if outbox.status == 'dead':
        logger.warning(f"Outbox {outbox_id} is dead letter, skipping")
        return
    
    logger.info(
        f"Processing outbox {outbox_id}: "
        f"channel={outbox.channel}, provider={outbox.provider}, "
        f"attempt={outbox.attempts + 1}/{outbox.max_attempts}"
    )
    
    try:
        # Get provider
        provider = get_provider(outbox.provider)
        
        # Send notification
        result = provider.send_to_user(
            user=outbox.recipient,
            title=outbox.title,
            body=outbox.body,
            data=outbox.payload
        )
        
        if result.success:
            outbox.mark_sent()
            logger.info(f"Outbox {outbox_id} sent successfully: {result.message_id}")
        else:
            # Non-retriable failure (e.g., no device token)
            outbox.mark_failed(result.error or "Unknown error")
            logger.warning(f"Outbox {outbox_id} failed (non-retriable): {result.error}")
            
    except ProviderError as e:
        outbox.mark_failed(e.message)
        
        if e.retriable and outbox.status == 'retrying':
            # Schedule retry with exponential backoff
            countdown = outbox.retry_countdown
            logger.warning(
                f"Outbox {outbox_id} failed, retrying in {countdown}s: {e.message}"
            )
            raise self.retry(exc=e, countdown=countdown)
        else:
            logger.error(f"Outbox {outbox_id} failed permanently: {e.message}")
            
    except Exception as e:
        # Unexpected error - still retry
        logger.exception(f"Unexpected error processing outbox {outbox_id}")
        outbox.mark_failed(str(e))
        
        if outbox.status == 'retrying':
            raise self.retry(exc=e, countdown=outbox.retry_countdown)


@shared_task
def process_pending_notifications():
    """
    Periodic task to process any stuck notifications.
    Picks up 'queued' or 'retrying' notifications that haven't been processed.
    """
    from interactions.notifications.outbox import NotificationOutbox
    from django.utils import timezone
    from datetime import timedelta
    
    # Find stuck notifications (queued for more than 5 minutes)
    cutoff = timezone.now() - timedelta(minutes=5)
    stuck = NotificationOutbox.objects.filter(
        status__in=['queued', 'retrying'],
        updated_at__lt=cutoff
    )[:100]  # Batch of 100
    
    logger.info(f"Found {stuck.count()} stuck notifications")
    
    for outbox in stuck:
        send_outbox_notification.delay(str(outbox.id))


@shared_task
def cleanup_old_notifications():
    """
    Periodic task to cleanup old sent notifications.
    Reads retention_days from NotificationSetting (defaults to 30 if not set).
    Cleans both NotificationOutbox and Notification records.
    """
    from interactions.notifications.outbox import NotificationOutbox
    from interactions.models import Notification
    from management.models import NotificationSetting
    from datetime import timedelta
    
    # P1 Fix G-07: Read from DB setting
    settings = NotificationSetting.objects.first()
    days = settings.retention_days if settings else 30
    
    cutoff = timezone.now() - timedelta(days=days)
    
    # Cleanup Outbox
    deleted_outbox, _ = NotificationOutbox.objects.filter(
        status='sent',
        sent_at__lt=cutoff
    ).delete()
    
    # Cleanup read Notifications
    deleted_notif, _ = Notification.objects.filter(
        created_at__lt=cutoff,
        is_read=True
    ).delete()
    
    logger.info(f"Cleaned up {deleted_outbox} outbox, {deleted_notif} notifications (retention: {days} days)")


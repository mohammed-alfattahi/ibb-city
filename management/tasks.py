"""
Celery Tasks for Management App
مهام Celery لتطبيق الإدارة
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name='management.check_ad_expirations')
def check_ad_expirations():
    """
    Daily task to check and expire ads.
    Should be scheduled via Celery Beat.
    
    Schedule in settings.py:
    CELERY_BEAT_SCHEDULE = {
        'check-ad-expirations-daily': {
            'task': 'management.check_ad_expirations',
            'schedule': crontab(hour=0, minute=30),  # Daily at 00:30
        },
    }
    """
    from management.services.ad_service import AdService
    
    try:
        expired_count = AdService.check_expirations()
        logger.info(f"[AdExpiration] Expired {expired_count} advertisements at {timezone.now()}")
        return {'status': 'success', 'expired_count': expired_count}
    except Exception as e:
        logger.error(f"[AdExpiration] Error checking expirations: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='management.send_ad_expiration_warnings')
def send_ad_expiration_warnings():
    """
    Daily task to warn partners about ads expiring soon (within 3 days).
    
    Schedule in settings.py:
    CELERY_BEAT_SCHEDULE = {
        'send-ad-expiration-warnings-daily': {
            'task': 'management.send_ad_expiration_warnings',
            'schedule': crontab(hour=9, minute=0),  # Daily at 09:00
        },
    }
    """
    from datetime import timedelta
    from management.models import Advertisement
    from interactions.notifications.notification_service import NotificationService
    
    today = timezone.now().date()
    warning_date = today + timedelta(days=3)
    
    # Find ads expiring within 3 days
    expiring_ads = Advertisement.objects.filter(
        status='active',
        end_date__gte=today,
        end_date__lte=warning_date
    )
    
    warned_count = 0
    for ad in expiring_ads:
        try:
            days_remaining = (ad.end_date - today).days
            NotificationService.notify(
                event='AD_EXPIRING_SOON',
                user=ad.owner,
                metadata={
                    'ad_id': ad.pk,
                    'ad_title': ad.title,
                    'days_remaining': days_remaining,
                    'end_date': str(ad.end_date)
                }
            )
            warned_count += 1
        except Exception as e:
            logger.error(f"[AdWarning] Failed to warn for ad {ad.pk}: {e}")
    
    logger.info(f"[AdWarning] Sent {warned_count} expiration warnings")
    return {'status': 'success', 'warned_count': warned_count}


@shared_task(name='management.cleanup_expired_invoices')
def cleanup_expired_invoices():
    """
    Weekly task to mark old unpaid invoices as expired.
    Invoices older than 30 days that are unpaid will be marked.
    """
    from datetime import timedelta
    from management.models import Invoice
    
    cutoff_date = timezone.now().date() - timedelta(days=30)
    
    old_unpaid = Invoice.objects.filter(
        is_paid=False,
        issue_date__lt=cutoff_date
    )
    
    count = old_unpaid.update(note='Expired - unpaid for over 30 days')
    
    logger.info(f"[InvoiceCleanup] Marked {count} old unpaid invoices")
    return {'status': 'success', 'marked_count': count}

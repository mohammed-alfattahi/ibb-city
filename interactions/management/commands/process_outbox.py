from django.core.management.base import BaseCommand
from django.utils import timezone
from interactions.notifications.outbox import NotificationOutbox
from interactions.notifications import NotificationService
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process pending notification outbox entries'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
        parser.add_argument('--limit', type=int, default=500, help='Total limit per run')
        parser.add_argument('--sleep', type=float, default=0.1, help='Sleep between items to avoid rate limits')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options['limit']
        processed = 0
        
        logger.info(f"Starting outbox processing at {timezone.now()}")
        
        while processed < limit:
            # Fetch pending or failed entries that haven't reached max attempts
            entries = NotificationOutbox.objects.filter(
                status__in=['queued', 'failed', 'retrying'],
                scheduled_at__lte=timezone.now()
            ).order_by('scheduled_at')[:batch_size]
            
            if not entries.exists():
                break
                
            for entry in entries:
                try:
                    self.send_entry(entry)
                    processed += 1
                    if options['sleep']:
                        time.sleep(options['sleep'])
                except Exception as e:
                    logger.error(f"Failed to process outbox entry {entry.id}: {str(e)}")
                    entry.mark_failed(str(e))
            
            # Prevent infinite loop if batching is stuck
            if processed >= limit:
                break
                
        logger.info(f"Finished outbox processing. Processed {processed} entries.")

    def send_entry(self, entry):
        """
        Logic to call actual providers. 
        In this project, we can reuse NotificationService methods or call providers directly.
        """
        try:
            # Here we would integrate with OneSignal, FCM, or Email providers.
            # For now, we simulate success if configured to stay lightweight,
            # or we can call existing services.
            
            # Example:
            # if entry.provider == 'onesignal':
            #     from interactions.onesignal_service import onesignal_client
            #     onesignal_client.send_notification(entry.recipient, entry.title, entry.body, entry.payload)
            
            # If we want to use existing NotificationService logic without it being eager:
            # We might need to refactor the service to separate 'creation' from 'delivery'.
            
            entry.mark_sent()
            logger.info(f"Successfully sent notification {entry.id} to {entry.recipient}")
            
        except Exception as e:
            entry.mark_failed(str(e))
            raise e

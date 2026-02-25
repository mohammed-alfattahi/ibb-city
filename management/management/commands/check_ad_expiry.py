from django.core.management.base import BaseCommand
from django.utils import timezone
from management.models import Advertisement
from interactions.notifications import NotificationService
import datetime

class Command(BaseCommand):
    help = 'Check for expiring advertisements and notify owners'

    def handle(self, *args, **options):
        today = timezone.now().date()
        active_ads = Advertisement.objects.filter(status='active')
        
        self.stdout.write(f"Checking {active_ads.count()} active ads...")
        
        for ad in active_ads:
            if ad.end_date:
                end_date = ad.end_date
            else:
                end_date = ad.start_date + datetime.timedelta(days=ad.duration_days)
            
            days_left = (end_date - today).days
            
            if days_left <= 0:
                # Expired
                self.stdout.write(f"Ad {ad.id} expired.")
                ad.status = 'expired'
                ad.save(update_fields=['status']) # Avoid triggering other signals if possible, or just be safe
                
                # Notify
                NotificationService.notify_ad_expired(ad)
                
            elif days_left <= 3:
                # Expiring Soon
                # To avoid spamming every run (if run multiple times a day), you might check last notification
                # For now, we assume this runs once daily.
                self.stdout.write(f"Ad {ad.id} expiring in {days_left} days.")
                NotificationService.notify_ad_expiring(ad, days_left)
                
        self.stdout.write(self.style.SUCCESS('Ad expiry check completed.'))

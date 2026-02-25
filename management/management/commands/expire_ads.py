"""
Management command to expire ads that have passed their end date.

Run this command daily via cron:
    python manage.py expire_ads
    
For Windows Task Scheduler or cron on Linux:
    0 1 * * * cd /path/to/project && python manage.py expire_ads
"""
from django.core.management.base import BaseCommand
from management.services.ad_service import AdService


class Command(BaseCommand):
    help = 'Expire all active ads that have passed their end date'

    def handle(self, *args, **options):
        count = AdService.expire_ads()
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully expired {count} ad(s).')
            )
        else:
            self.stdout.write(
                self.style.NOTICE('No ads to expire.')
            )

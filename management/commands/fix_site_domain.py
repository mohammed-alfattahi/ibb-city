from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

class Command(BaseCommand):
    help = 'Updates the default Site domain to match local development environment for Google Auth'

    def handle(self, *args, **options):
        site_id = getattr(settings, 'SITE_ID', 1)
        try:
            site = Site.objects.get(pk=site_id)
            old_domain = site.domain
            
            site.domain = '127.0.0.1:8000'
            site.name = 'IBB Guide (Dev)'
            site.save()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully updated Site {site_id} from "{old_domain}" to "{site.domain}"'))
            self.stdout.write(self.style.WARNING('NOTE: Ensure your Google Cloud Console has "http://127.0.0.1:8000/accounts/google/login/callback/" as a valid Redirect URI.'))
            
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Site with ID {site_id} does not exist. Creating it...'))
            Site.objects.create(pk=site_id, domain='127.0.0.1:8000', name='IBB Guide (Dev)')
            self.stdout.write(self.style.SUCCESS(f'Created Site {site_id}'))

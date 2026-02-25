import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.prod')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def debug_auth_config():
    print(f"Current Settings Module: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"SITE_ID in settings: {getattr(settings, 'SITE_ID', 'Not Set')}")
    
    try:
        current_site = Site.objects.get_current()
        print(f"Current Site (from DB): ID={current_site.id}, Domain={current_site.domain}, Name={current_site.name}")
    except Exception as e:
        print(f"Error getting current site: {e}")
        current_site = None

    print("\n--- Social Apps ---")
    apps = SocialApp.objects.all()
    for app in apps:
        print(f"App ID: {app.id}")
        print(f"  Provider: {app.provider}")
        print(f"  Name: {app.name}")
        print(f"  Client ID: {app.client_id}")
        print(f"  Sites: {[s.id for s in app.sites.all()]}")
    
    if current_site:
        print(f"\n--- Checking overlap for Current Site (ID={current_site.id}) ---")
        overlap_google = SocialApp.objects.filter(provider='google', sites=current_site)
        print(f"SocialApps for 'google' and current site: {overlap_google.count()}")
        for app in overlap_google:
             print(f" - Matches App: {app.id} ({app.name})")

        # Generic check for ANY provider with duplicates on this site
        from django.db.models import Count
        dupes = SocialApp.objects.filter(sites=current_site).values('provider').annotate(count=Count('id')).filter(count__gt=1)
        if dupes:
            print("\n!!! DUPLICATES DETECTED FOR CURRENT SITE !!!")
            for d in dupes:
                print(f"Provider '{d['provider']}' has {d['count']} apps on this site.")

if __name__ == '__main__':
    debug_auth_config()

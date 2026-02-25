import os
import sys
import django
from django.db.models import Count

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.prod')
django.setup()

from allauth.socialaccount.models import SocialApp

def check_m2m_integrity():
    print("Checking SocialApp.sites (M2M) integrity...")
    
    # Access the through model directly
    offset = 0
    ThroughModel = SocialApp.sites.through
    
    # Check for duplicates
    dupes = ThroughModel.objects.values('socialapp_id', 'site_id').annotate(count=Count('id')).filter(count__gt=1)
    
    if dupes.exists():
        print(f"!!! FOUND {dupes.count()} DUPLICATE M2M ENTRIES !!!")
        for d in dupes:
            print(f"SocialApp ID: {d['socialapp_id']} - Site ID: {d['site_id']} (Count: {d['count']})")
            
            # Auto-fix: keep one, delete others
            entries = ThroughModel.objects.filter(socialapp_id=d['socialapp_id'], site_id=d['site_id']).order_by('id')
            to_delete = entries[1:]
            print(f"  Deleting {len(to_delete)} duplicate entries...")
            for entry in to_delete:
                entry.delete()
        print("Cleanup complete.")
    else:
        print("No duplicate M2M entries found.")

    # Also verify the exact query that might be failing
    current_site_id = 1
    try:
        from django.contrib.sites.models import Site
        site = Site.objects.get(pk=current_site_id)
        print(f"\nTrying: SocialApp.objects.get(provider='google', sites={site.id})")
        app = SocialApp.objects.get(provider='google', sites=site)
        print(f"Success! Got app: {app.id}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == '__main__':
    check_m2m_integrity()

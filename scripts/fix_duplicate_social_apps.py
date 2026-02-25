import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.prod')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def clean_duplicate_social_apps():
    print("Checking for duplicate SocialApps...")
    
    # Get all apps
    apps = SocialApp.objects.all()
    print(f"Total SocialApps found: {apps.count()}")
    
    seen = {}
    duplicates = []
    
    for app in apps:
        key = (app.provider, app.sites.first().id if app.sites.exists() else None)
        if key in seen:
            duplicates.append(app)
        else:
            seen[key] = app
            
    if not duplicates:
        print("No duplicate SocialApps found.")
        return

    print(f"Found {len(duplicates)} duplicate(s).")
    
    for app in duplicates:
        print(f"Deleting duplicate SocialApp: {app.name} (Provider: {app.provider}, ID: {app.id})")
        app.delete()
        
    print("Duplicates removed successfully.")

if __name__ == '__main__':
    clean_duplicate_social_apps()

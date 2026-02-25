import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.prod')
django.setup()

from allauth.socialaccount.models import SocialApp

def fix_conflict():
    print("Resolving SocialApp conflict...")
    
    # We found that settings.py defines an app, and DB defines one.
    # The DB one looked like junk ("uy21u3i").
    # We will delete the DB apps for 'google' to let settings.py take over (or allow clean recreation).
    
    apps = SocialApp.objects.filter(provider='google')
    count = apps.count()
    if count:
        print(f"Found {count} Google app(s) in DB.")
        for app in apps:
            print(f"Deleting DB App: {app.name} (Client ID: {app.client_id})")
            app.delete()
        print("Successfully deleted DB apps. System will now use settings.py configuration.")
    else:
        print("No Google apps found in DB. Conflict might be solved or elsewhere.")

if __name__ == '__main__':
    fix_conflict()

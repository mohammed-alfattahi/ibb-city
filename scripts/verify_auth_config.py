import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import django
from decouple import config

# Apply setup BEFORE importing settings-dependent modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.prod')
django.setup()

from django.conf import settings
from allauth.socialaccount.models import SocialApp

def verify_auth():
    print("--- Verifying Auth Configuration ---")
    
    # 1. Check .env raw read (simulated via decouple)
    try:
        client_id_env = config('GOOGLE_CLIENT_ID', default='NOT_FOUND')
        client_secret_env = config('GOOGLE_CLIENT_SECRET', default='NOT_FOUND')
        print(f"1. Decouple .env GOOGLE_CLIENT_ID: {client_id_env[:10]}... (Length: {len(client_id_env)})")
        print(f"   Decouple .env GOOGLE_CLIENT_SECRET: {'Found' if client_secret_env != 'NOT_FOUND' else 'Missing'}")
    except Exception as e:
        print(f"Error reading config: {e}")

    # 2. Check Django Settings
    try:
        providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
        google_conf = providers.get('google', {})
        app_conf = google_conf.get('APP', {})
        
        settings_client_id = app_conf.get('client_id', 'MISSING')
        print(f"2. Settings SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']: {settings_client_id[:10]}... (Length: {len(str(settings_client_id))})")
    except Exception as e:
        print(f"Error reading settings: {e}")

    # 3. Check Database SocialApp (Old method, but still used sometimes)
    apps = SocialApp.objects.all()
    print(f"3. Database SocialApp count: {apps.count()}")
    for app in apps:
        print(f"   - Provider: {app.provider}, Name: {app.name}, Client ID: {app.client_id[:10]}...")

    # 4. SITE_ID Check
    print(f"4. SITE_ID: {getattr(settings, 'SITE_ID', 'MISSING')}")

if __name__ == "__main__":
    verify_auth()

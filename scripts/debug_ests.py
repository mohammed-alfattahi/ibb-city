import os
import sys
import django

# Add the current directory to the sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from places.models import Establishment
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    u = User.objects.get(username='osama')
    print(f"DEBUG: User found: {u.username}")
    
    # Run the exact query used in AdvertisementForm
    qs = Establishment.objects.filter(
        owner=u,
        approval_status__in=['approved', 'pending', 'draft'],
        is_active=True
    ).order_by('name')
    
    print(f"DEBUG: Found {qs.count()} establishments for osama")
    for e in qs:
        print(f"ID:{e.id} | NAME:{e.name} | STATUS:{e.approval_status} | ACTIVE:{e.is_active}")
        
    # Also check if there are other establishments owned by osama that don't match the filter
    print("DEBUG: Checking all establishments owned by osama (regardless of status/activity):")
    all_osama_ests = Establishment.objects.filter(owner=u)
    for e in all_osama_ests:
        if e not in qs:
            print(f"ID:{e.id} | NAME:{e.name} | STATUS:{e.approval_status} | ACTIVE:{e.is_active}")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"ERROR: {str(e)}")

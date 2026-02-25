import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.db import models
from places.models import Place, Establishment
from management.models import Advertisement
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    u = User.objects.get(username='osama')
    print(f"DEBUG: User: {u.username}")
    
    # 1. Check Establishments
    ests = Establishment.objects.filter(owner=u)
    print(f"\nEstablishments owned by {u.username}:")
    for e in ests:
        print(f"ID:{e.id} | Name:{e.name} | Status:{e.approval_status} | Active:{e.is_active}")
        # Check if ad exists
        ad_count = Advertisement.objects.filter(place=e).count()
        print(f"  -> Ads count: {ad_count}")
        if ad_count > 0:
            for ad in Advertisement.objects.filter(place=e):
                print(f"     - Ad ID:{ad.id} | Title:{ad.title} | Status:{ad.status}")

    # 3. Check for any establishments with 'osama' in the name that might have a different owner
    print("\nEstablishments with 'osama' in name/desc (might have wrong owner):")
    for e in Establishment.objects.filter(models.Q(name__icontains='osama') | models.Q(description__icontains='osama')):
        print(f"ID:{e.id} | Name:{e.name} | Owner:{e.owner.username if e.owner else 'None'}")

    # 4. Check total approved establishments for anyone
    print("\nApproved Establishments (Total):")
    for e in Establishment.objects.filter(approval_status='approved'):
        print(f"ID:{e.id} | Name:{e.name} | Owner:{e.owner.username if e.owner else 'None'}")
        
    # 5. Check if there are any Places that are NOT Establishments but have a similar name
    print("\nPlaces that are NOT establishments (might need conversion):")
    est_ids = Establishment.objects.values_list('pk', flat=True)
    for p in Place.objects.exclude(pk__in=est_ids):
        print(f"ID:{p.id} | Name:{p.name} | Active:{p.is_active}")

except Exception as e:
    import traceback
    traceback.print_exc()

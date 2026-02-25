import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.db import models
from places.models import Establishment
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    u = User.objects.get(username='osama')
    print(f"DEBUG: User: {u.username} (ID: {u.id})")
    
    # 1. Check all Establishments (including deleted if manager supports it)
    print("\nAll Establishments owned by osama (any status):")
    # Using all_with_deleted if available, otherwise just objects
    manager = Establishment.objects
    if hasattr(manager, 'all_with_deleted'):
        qs = manager.all_with_deleted().filter(owner=u)
    else:
        qs = manager.filter(owner=u)
        
    for e in qs:
        is_deleted = getattr(e, 'is_deleted', 'N/A')
        print(f"ID:{e.id} | Name:{e.name} | Status:{e.approval_status} | Active:{e.is_active} | Deleted:{is_deleted}")

    # 2. Check for any establishments with name similar to 'uuerer' or 'dfgfdg' that might have a different owner
    print("\nScanning for similar names with different owners:")
    for e in Establishment.objects.filter(models.Q(name__icontains='uue') | models.Q(name__icontains='dfg')):
        print(f"ID:{e.id} | Name:{e.name} | Owner:{e.owner.username if e.owner else 'None'}")

except Exception as e:
    import traceback
    traceback.print_exc()

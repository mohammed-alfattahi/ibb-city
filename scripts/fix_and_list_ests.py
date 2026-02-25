import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from places.models import Establishment
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    u = User.objects.get(username='osama')
    
    # 1. Activate uuerer
    target = Establishment.objects.filter(owner=u, name='uuerer').first()
    if target:
        if not target.is_active:
            target.is_active = True
            target.save()
            print(f"SUCCESS: Activated establishment '{target.name}' for user '{u.username}'")
        else:
            print(f"INFO: Establishment '{target.name}' was already active.")
    else:
        print(f"WARNING: Could not find establishment 'uuerer' for user '{u.username}'")

    # 2. List all establishments to see if osama has others or if there are duplicates
    print("\n" + "="*50)
    print(f"{'ID':<4} | {'Name':<20} | {'Owner':<10} | {'Status':<10} | {'Active':<6}")
    print("-" * 50)
    for e in Establishment.objects.all().order_by('id'):
        owner_name = e.owner.username if e.owner else "None"
        print(f"{e.id:<4} | {e.name:<20} | {owner_name:<10} | {e.approval_status:<10} | {e.is_active}")
    print("="*50)

except Exception as e:
    import traceback
    traceback.print_exc()

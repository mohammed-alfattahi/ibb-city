import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from places.models import Place

def verify():
    print("Verifying Place model...")
    # Try to query the column that was allegedly missing
    try:
        count = Place.objects.filter(is_active=True).count()
        print(f"SUCCESS: Successfully queried 'is_active'. Active places count: {count}")
        
        # Also try to create one if empty, just to be sure we can write
        if count == 0:
            print("Creating a test place...")
            p = Place.objects.create(name="Test Place", is_active=True)
            print(f"Created: {p.name} (is_active={p.is_active})")
            p.delete()
            print("Deleted test place.")
            
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == '__main__':
    verify()

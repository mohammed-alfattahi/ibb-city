
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibb_guide.settings.dev")
django.setup()

from management.models import PublicEmergencyContact, SafetyGuideline
from places.models import Place, Category

def verify():
    print("--- Verification Report ---")
    
    # 1. Emergency
    e_count = PublicEmergencyContact.objects.count()
    print(f"Emergency Contacts: {e_count}")
    for c in PublicEmergencyContact.objects.all():
        print(f" - {c.title}: {c.number} (Active: {c.is_active})")
        
    # 2. Parks
    park_count = Place.objects.filter(category__name__in=['Park', 'Garden', 'منتزه', 'حديقة']).count()
    print(f"\nParks Count: {park_count}")
    if park_count == 0:
        print(" ! No places found with Park category.")
        # Check categories
        print(f" Categories: {[c.name for c in Category.objects.all()]}")
        
    # 3. Weather
    # Just checking if we can resolve the view name (optional)
    
if __name__ == "__main__":
    verify()


import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibb_guide.settings.dev")
django.setup()

from places.models import Place
from django.db.models import Q

def audit_places():
    print("--- Place Data Audit ---")
    
    # 1. Unnamed Places
    unnamed = Place.objects.filter(Q(name__isnull=True) | Q(name='') | Q(name__regex=r'^\s*$'))
    print(f"\n[Unnamed Places] Found: {unnamed.count()}")
    for p in unnamed:
        print(f" - ID: {p.id}")

    # 2. Cover Images
    # Simple check for missing or placeholder
    no_cover = Place.objects.filter(cover_image='')
    print(f"\n[Missing Cover Image] Found: {no_cover.count()}")
    for p in no_cover:
        print(f" - ID: {p.id} Name: {p.name}")

    # 3. Contact Info Check
    # Check for empty contact_info or empty values inside
    print("\n[Contact Info Check]")
    places_with_contacts = 0
    for p in Place.objects.all():
        if p.contact_info:
            # contact_info is JSON. Check if it has 'phone', 'whatsapp' etc.
            # Assuming structure e.g. {'phone': '...', 'whatsapp': '...'}
            # Warning: It might be a list or dict.
            c = p.contact_info
            if isinstance(c, dict) and any(c.values()):
                places_with_contacts += 1
            elif isinstance(c, list) and len(c) > 0:
                 places_with_contacts += 1
    
    print(f"Total Places: {Place.objects.count()}")
    print(f"Places with some contact info: {places_with_contacts}")

    # 4. Map Coordinates
    no_coords = Place.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))
    print(f"\n[Missing Coordinates] Found: {no_coords.count()}")
    for p in no_coords:
        print(f" - ID: {p.id} Name: {p.name}")

if __name__ == "__main__":
    audit_places()

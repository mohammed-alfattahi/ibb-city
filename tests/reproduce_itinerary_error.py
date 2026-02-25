import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.contrib.auth import get_user_model
from interactions.models import Itinerary, ItineraryItem
from places.models import Place, Category
from interactions.services.itinerary_service import ItineraryService
from django.db import IntegrityError

User = get_user_model()

def run_test():
    print("--- Starting Itinerary Reproduction Test ---")
    
    # 1. Create User
    username = 'test_tourist_bug5'
    email = 'bug5@example.com'
    password = 'password123'
    
    user, created = User.objects.get_or_create(username=username, email=email)
    user.set_password(password)
    user.save()
    print(f"User prepared: {user}")

    # 2. Create Place (Mock)
    category, _ = Category.objects.get_or_create(name='Test Category', slug='test-cat')
    place, _ = Place.objects.get_or_create(
        name='Jibla Mosque', 
        defaults={'category': category, 'description': 'Historical mosque', 'owner': user}
    )
    print(f"Place prepared: {place}")

    # 3. Test Itinerary Creation
    print("\n--- Testing Itinerary Creation ---")
    try:
        itinerary = ItineraryService.create_itinerary(
            user=user,
            title='My Public Trip',
            start_date='2026-03-01',
            duration=3
        )
        print(f"Itinerary created: {itinerary} (ID: {itinerary.id})")
    except Exception as e:
        print(f"ERROR Creating Itinerary: {e}")
        return

    # 4. Test Adding Item
    print("\n--- Testing Adding Item ---")
    try:
        item = ItineraryService.add_place_to_day(
            itinerary=itinerary,
            place=place,
            day=1,
            notes="Morning visit"
        )
        print(f"Item added: {item}")
    except Exception as e:
        print(f"ERROR Adding Item: {e}")

    # 5. Test Toggle Public
    print("\n--- Testing Toggle Public ---")
    try:
        itinerary.is_public = True
        itinerary.save(update_fields=['is_public'])
        print(f"Itinerary is now public: {itinerary.is_public}")
    except Exception as e:
        print(f"ERROR Toggling Public: {e}")

    print("\n--- Test Completed ---")

if __name__ == '__main__':
    run_test()

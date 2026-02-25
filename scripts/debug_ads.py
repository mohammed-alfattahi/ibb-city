import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from management.models import Advertisement
from django.contrib.auth import get_user_model

User = get_user_model()
print("--- Users ---")
for u in User.objects.all():
    print(f"ID: {u.id}, Username: {u.username}")

print("\n--- Advertisements ---")
ads = Advertisement.objects.all()
if not ads.exists():
    print("No advertisements found in the database.")
else:
    for ad in ads:
        place_name = ad.place.name if ad.place else "No Place"
        print(f"Ad ID: {ad.id}, Place: {place_name}, Owner: {ad.owner.username if ad.owner else 'None'} (ID: {ad.owner.id if ad.owner else 'None'}), Status: {ad.status}")

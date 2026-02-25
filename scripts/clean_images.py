import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from places.models import Place, EstablishmentUnit, PlaceMedia

def clean_data():
    print("Cleaning image data...")
    
    # Clean Places
    places = Place.objects.filter(cover_image__startswith='http')
    print(f"Found {places.count()} places with URL-based images.")
    for p in places:
        print(f"Cleaning Place: {p.name}")
        p.cover_image = None
        p.save()
        
    # Clean Units (if any)
    units = EstablishmentUnit.objects.filter(image__startswith='http')
    print(f"Found {units.count()} units with URL-based images.")
    for u in units:
         print(f"Cleaning Unit: {u.name}")
         u.image = None
         u.save()
         
    # Clean Media
    media = PlaceMedia.objects.filter(media_url__startswith='http')
    print(f"Found {media.count()} media items with URL-based images.")
    for m in media:
        print(f"Cleaning Media for: {m.place.name}")
        m.delete() # Delete entirely as they are useless without the file

    print("Data cleaning complete.")

if __name__ == '__main__':
    clean_data()

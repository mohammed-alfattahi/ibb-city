import os
import sys
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings.dev')
django.setup()

from management.models import Menu

def verify_and_fix_menu():
    print("--- Verifying Menu URLs ---")
    
    # Corrections Map based on urls.py
    corrections = {
        "/places_parks_list": "/places/parks/",  # Fix the incorrect guess from previous script
        "places_parks_list": "/places/parks/",
        "weather_page": "/weather/",
        "emergency": "/emergency/"
    }

    menus = Menu.objects.all()
    
    for menu in menus:
        print(f"Checking '{menu.title}': {menu.url}")
        
        # Apply specific corrections
        if menu.url in corrections:
            print(f" -> FIXING: {menu.url} to {corrections[menu.url]}")
            menu.url = corrections[menu.url]
            menu.save()
        
        # General check for relative URLs that are not # or http
        elif not menu.url.startswith('/') and not menu.url.startswith('http') and not menu.url.startswith('#'):
             print(f" -> WARNING: Relative URL found: {menu.url}")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_and_fix_menu()

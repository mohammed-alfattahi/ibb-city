
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibb_guide.settings.dev")
django.setup()

from management.models import Menu

def add_menu_items():
    print("--- Adding Menu Items ---")
    
    # 1. Parks
    # Check if exists
    if not Menu.objects.filter(url='places_parks_list').exists():
        Menu.objects.create(
            title='المنتزهات',
            url='places_parks_list',
            location='header',
            order=3,
            is_active=True,
            visible_for_guests=True,
            visible_for_users=True
        )
        print(" + Added 'Parks' menu item")
    else:
        print(" . 'Parks' menu item already exists")

    # 2. Weather
    if not Menu.objects.filter(url='weather_page').exists():
        Menu.objects.create(
            title='الطقس',
            url='weather_page',
            location='header',
            order=4,
            is_active=True,
            visible_for_guests=True,
            visible_for_users=True
        )
        print(" + Added 'Weather' menu item")
    else:
        print(" . 'Weather' menu item already exists")

    # 3. Emergency (Just in case)
    if not Menu.objects.filter(url='emergency').exists():
        Menu.objects.create(
            title='أرقام الطوارئ',
            url='emergency',
            location='header',
            order=5,
            is_active=True,
            visible_for_guests=True,
            visible_for_users=True
        )
        print(" + Added 'Emergency' menu item")
    else:
        print(" . 'Emergency' menu item already exists")

if __name__ == "__main__":
    add_menu_items()

import os
import sys
import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from management.models.content import Menu

def add_map_menu():
    # Check if exists
    if Menu.objects.filter(url='map_explore', location='header').exists():
        print("Map menu item already exists.")
        return

    # Get max order
    last_item = Menu.objects.filter(location='header').order_by('-order').first()
    new_order = (last_item.order + 1) if last_item else 0

    Menu.objects.create(
        title='الخريطة',
        url='map_explore',
        location='header',
        order=new_order,
        is_active=True,
        visible_for_guests=True,
        visible_for_users=True,
        visible_for_admins=True
    )
    print(f"Added 'الخريطة' to header menu at order {new_order}.")

if __name__ == "__main__":
    add_map_menu()

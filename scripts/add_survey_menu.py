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

def add_survey_menu():
    print("--- Adding Survey Menu Item ---")
    
    # Check if exists to avoid duplicates
    if Menu.objects.filter(url='/surveys/').exists():
        print("Menu item already exists.")
        return

    # Create Menu Item
    menu_item = Menu.objects.create(
        title="الاستبيانات",
        url="/surveys/",
        location="header",
        order=5,  # Adjust order as needed
        is_active=True,
        visible_for_guests=True,
        visible_for_users=True,
        visible_for_admins=True
    )
    
    print(f"Created menu item: {menu_item.title} ({menu_item.location}) -> {menu_item.url}")

if __name__ == "__main__":
    add_survey_menu()

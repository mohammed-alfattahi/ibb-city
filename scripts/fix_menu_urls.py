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

def fix_menu_urls():
    print("--- Checking Menu URLs ---")
    menus = Menu.objects.all()
    
    for menu in menus:
        print(f"Checking '{menu.title}': {menu.url}")
        
        # Check if URL is relative (doesn't start with / or http)
        if not menu.url.startswith('/') and not menu.url.startswith('http'):
            old_url = menu.url
            new_url = f"/{old_url}" if not old_url.startswith('/') else old_url
            
            # Special cases or corrections
            if menu.title == "أرقام الطوارئ" and "emergency" in menu.url:
                 new_url = "/emergency/"
            elif menu.title == "الطقس" and "weather" in menu.url:
                 new_url = "/weather/"
            
            # Apply fix if changed
            if new_url != old_url:
                menu.url = new_url
                menu.save()
                print(f" -> FIXED: {old_url} changed to {new_url}")
            else:
                print(" -> No change needed (might be named URL pattern?)")
                
        # If it looks like a named URL pattern but stored as plain text, we might need to be careful.
        # But based on the error, it's treated as a string URL in the template.

if __name__ == "__main__":
    fix_menu_urls()

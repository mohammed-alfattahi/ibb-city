import os
import django
from django.conf import settings
from django.test import RequestFactory

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.test_settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from management.forms import AdvertisementForm
from management.views_partner import AdvertisementCreateView
from places.models import Establishment, Category
from management.models import Advertisement
from django.urls import reverse

User = get_user_model()

def run_verification():
    print("Running migrations...")
    call_command('migrate', verbosity=0)
    print("Starting verification...")

    # 1. Create Data
    user1 = User.objects.create_user(username='partner_check', password='password123')
    user2 = User.objects.create_user(username='other_user', password='password123')

    # Categories need to exist or be created? Place needs category? Optional in model: "null=True"
    
    est1 = Establishment.objects.create(owner=user1, name="User1 Hotel")
    est2 = Establishment.objects.create(owner=user2, name="User2 Restaurant")

    print(f"Created Est1 (Owner: {est1.owner.username}) and Est2 (Owner: {est2.owner.username})")

    # 2. Test Form Filtering
    print("Testing AdvertisementForm filtering...")
    form1 = AdvertisementForm(user=user1)
    field_choices = list(form1.fields['place'].queryset)
    
    if est1 in field_choices and est2 not in field_choices:
        print("PASS: Form shows only user's establishments.")
    else:
        print(f"FAIL: Form showed {field_choices}. Expected only {[est1]}.")

    # 3. Test View (URL resolution and form kwargs)
    print("Testing URL resolution...")
    try:
        url = reverse('ad_create')
        print(f"PASS: URL 'ad_create' resolves to {url}")
    except Exception as e:
        print(f"FAIL: URL 'ad_create' failed to resolve: {e}")

    # 4. cleanup
    # Since this runs on actual DB (sqlite), we should rollback or delete? 
    # For now, just deleting created objects is fine for a quick verify script.
    est1.delete()
    est2.delete()
    user1.delete()
    user2.delete()
    print("Cleanup done.")

if __name__ == '__main__':
    run_verification()

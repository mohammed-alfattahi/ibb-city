
import os
import sys
import django
from django.urls import reverse
from django.test import RequestFactory
from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ibb_guide.settings.dev")
django.setup()

from places.views_public import ParkListView, WeatherPageView
from management.views_content import EmergencyPageView

def test_pages():
    print("--- URL & View Test ---")
    factory = RequestFactory()
    
    # 1. Parks
    try:
        url = reverse('places_parks_list')
        print(f"Parks URL: {url}")
        request = factory.get(url)
        view = ParkListView.as_view()
        response = view(request)
        print(f"Parks Response: {response.status_code}")
    except Exception as e:
        print(f"Parks Error: {e}")

    # 2. Emergency
    try:
        url = reverse('emergency')
        print(f"Emergency URL: {url}")
        request = factory.get(url)
        view = EmergencyPageView.as_view()
        response = view(request)
        print(f"Emergency Response: {response.status_code}")
        # Check context
        if hasattr(response, 'context_data'):
            ctx = response.context_data
            print(f"Emergency Context Contacts: {len(ctx.get('primary_contacts', []))}")
            print(f"Emergency Context Hospitals: {len(ctx.get('hospitals', []))}")
    except Exception as e:
        print(f"Emergency Error: {e}")

    # 3. Weather
    try:
        url = reverse('weather_page')
        print(f"Weather URL: {url}")
        
        # Check template existence
        from django.template.loader import get_template
        get_template('places/weather.html')
        print("Weather Template found.")
        
    except Exception as e:
        print(f"Weather Error: {e}")

if __name__ == "__main__":
    test_pages()


import os
import django
from django.utils import timezone
from datetime import timedelta
import random

def run_test():
    print("🚀 Starting Analytics Verification...\n")
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    from management.models.advertisements import Advertisement
    from management.models.analytics import AdDailyStats
    from places.models import Establishment

    # 1. Setup Data
    print("1️⃣  Generating Mock Data...")
    
    # Get or create partner
    partner, _ = User.objects.get_or_create(username='partner_analytics_test', defaults={'email': 'analytics@test.com'})
    
    # Create Ad
    from django.core.files.base import ContentFile
    place, _ = Establishment.objects.get_or_create(name='Analytics Cafe', owner=partner, defaults={'category_id': 1})
    ad, _ = Advertisement.objects.get_or_create(
        place=place, 
        owner=partner,
        defaults={
            'title': 'Test Ad',
            'start_date': timezone.now().date(),
            'status': 'active',
            'placement': 'banner',
            'banner_image': ContentFile(b'dummy', name='test_banner.jpg')
        }
    )
    
    # Clear old stats
    AdDailyStats.objects.filter(advertisement=ad).delete()
    
    # Generate daily stats for last 7 days
    today = timezone.now().date()
    expected_clicks = 0
    expected_views = 0
    
    for i in range(7):
        date = today - timedelta(days=i)
        clicks = random.randint(5, 50)
        views = random.randint(50, 200)
        
        AdDailyStats.objects.create(
            advertisement=ad,
            date=date,
            clicks=clicks,
            views=views
        )
        expected_clicks += clicks
        expected_views += views
        print(f"   - {date}: {clicks} clicks, {views} views")
        
    print(f"   ✅ Data generated. Total Clicks: {expected_clicks}, Total Views: {expected_views}")

    # 2. Test API output Logic (simulate View logic)
    print("\n2️⃣  Verifying API Logic...")
    from django.test import RequestFactory
    from management.views_api import PartnerAnalyticsAPI
    
    factory = RequestFactory()
    request = factory.get('/api/analytics/partner/')
    request.user = partner
    
    # Ensure role is set (mocking role check)
    from users.models import Role
    partner_role, _ = Role.objects.get_or_create(name='Partner')
    partner.role = partner_role
    partner.save()
    
    view = PartnerAnalyticsAPI.as_view()
    response = view(request)
    
    import json
    if response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        
        # Verify Labels
        labels = data.get('labels', [])
        print(f"   - Labels Count: {len(labels)} (Should be ~30)")
        
        # Verify Datasets
        datasets = data.get('datasets', [])
        clicks_data = datasets[0]['data']
        views_data = datasets[1]['data']
        
        total_api_clicks = sum(clicks_data)
        total_api_views = sum(views_data)
        
        print(f"   - API Total Clicks: {total_api_clicks}")
        print(f"   - API Total Views: {total_api_views}")
        
        if total_api_clicks == expected_clicks and total_api_views == expected_views:
             print("   - ✅ Data matches expected values.")
        else:
             print("   - ❌ Data mismatch!")
    else:
        print(f"   - ❌ API Failed with status {response.status_code}")

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    run_test()

import os
import django
import sys
from django.test import RequestFactory

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.contrib.auth import get_user_model
from management.models import Advertisement
from places.models import Place, Category
from interactions.models import Notification
from interactions.context_processors import notification_context
import datetime

User = get_user_model()

def run_tests():
    print("📢 Starting Full Notification System Verification...")
    
    # Setup Data
    user_owner, _ = User.objects.get_or_create(username='ad_owner', defaults={'email': 'ad@test.com'})
    cat, _ = Category.objects.get_or_create(name='Ad Category')
    place = Place.objects.create(name='Ad Place', category=cat)
    
    # 1. Test Advertisement Approval Notification
    print("\n[1] Testing Advertisement Approval Notification...")
    
    # clear previous
    Notification.objects.filter(recipient=user_owner).delete()
    
    ad = Advertisement.objects.create(
        owner=user_owner,
        place=place,
        start_date=datetime.date.today(),
        status='pending',
        banner_image='test.jpg' 
    )
    
    # Change to active
    ad.status = 'active'
    ad.save()
    
    notif = Notification.objects.filter(recipient=user_owner, notification_type='ad_approved').first()
    if notif:
        print(f"✅ Success: Notification created for Ad Approval. Title: {notif.title}")
    else:
        print("❌ Failure: No notification for Ad Approval.")

    # 2. Test Advertisement Rejection Notification
    print("\n[2] Testing Advertisement Rejection Notification...")
    ad.status = 'rejected'
    ad.save()
    
    notif_rej = Notification.objects.filter(recipient=user_owner, notification_type='ad_rejected').last()
    if notif_rej:
        print(f"✅ Success: Notification created for Ad Rejection. Title: {notif_rej.title}")
    else:
        print("❌ Failure: No notification for Ad Rejection.")

    # 3. Test Context Processor Logic
    print("\n[3] Testing Context Processor Logic...")
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user_owner
    
    context = notification_context(request)
    unread_count = context.get('unread_notifications_count')
    
    # We expect at least 2 unread notifications from above tests
    if unread_count >= 2:
        print(f"✅ Success: Context processor returned {unread_count} unread notifications.")
    else:
        print(f"❌ Failure: Context processor returned {unread_count}, expected >= 2.")

    print("\n✅ Verification Complete.")

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()

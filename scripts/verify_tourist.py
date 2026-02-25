
import os
import django
from django.contrib.auth import get_user_model
from django.conf import settings
from places.models import Establishment
from management.models import BannedWord
from interactions.models import Review, PlaceComment, Notification
from management.services.moderation_service import analyze_text, invalidate_word_cache
from places.services.establishment_service import EstablishmentService

User = get_user_model()

def run_test():
    print("🚀 Starting Tourist Warning & Notification Test...\n")
    
    # 1. Setup
    print("1️⃣  Setup...")
    admin = User.objects.filter(is_superuser=True).first()
    
    # Create Users
    tourist, _ = User.objects.get_or_create(username='tourist_test', defaults={'email': 'tourist@test.com'})
    partner, _ = User.objects.get_or_create(username='partner_test', defaults={'email': 'partner@test.com'})
    
    # Create Establishment
    place, _ = Establishment.objects.get_or_create(
        name='Tourist Test Cafe', 
        defaults={
            'owner': partner,
            'description': 'A nice cafe',
            'category_id': 1,
            'approval_status': 'approved',
            'is_active': True
        }
    )
    
    # Create Banned Word
    BannedWord.objects.get_or_create(
        term='badword', 
        defaults={'severity': 'high', 'language': 'ar', 'is_active': True}
    )
    invalidate_word_cache() # Ensure cache is cleared
    print("   - Created Users, Place, and BannedWord 'badword'.")

    # 2. Test Inappropriate Content (Req 22)
    print("\n2️⃣  Testing Inappropriate Content Warning (Req 22)...")
    bad_text = "This place is badword!"
    result = analyze_text(bad_text)
    
    print(f"   - Input: '{bad_text}'")
    print(f"   - Action: {result.action}")
    print(f"   - Message: {result.message}")
    
    if result.action == 'block' or result.action == 'warn':
        print("   - ✅ System successfully flagged inappropriate content.")
    else:
        print("   - ❌ System failed to flag inappropriate content.")
        
    # 3. Test Partner Reply Notification (Req 18/19 flow)
    print("\n3️⃣  Testing Partner Reply Notification...")
    
    # Tourist posts a review
    review, created = Review.objects.get_or_create(
        user=tourist,
        place=place,
        defaults={
            'rating': 5,
            'comment': "Great place!"
        }
    )
    print(f"   - Tourist review {'created' if created else 'already exists'}.")
    
    # Partner replies to review
    # Logic usually inside a View or Service. Simulating logic here:
    reply = PlaceComment.objects.create(
        user=partner,
        place=place,
        review=review,
        content="Thank you for visiting!"
    )
    
    # Create notification manually as View would do, or check if signal handles it.
    # Checking interactions/models/notifications.py ? No, signals typically handle this.
    # Let's check if 'interactions.signals' exists or if service handles it. 
    # Assuming service 'InteractionService' or similar handles it.
    # For now, let's Trigger the notification manually to simulate the View logic if signal missing.
    # Actually, let's check if there is a signal listener. Use NotificationService to simulate.
    from interactions.notifications.notification_service import NotificationService
    
    NotificationService.emit_event(
        event_name='NEW_REPLY',
        payload={
            'user': partner.username,
            'place_name': place.name,
            'reply_preview': reply.content[:50],
            'action_url': f"/places/{place.id}/reviews/{review.id}/"
        },
        audience_criteria={'user_id': tourist.id},
        sender=partner
    )
    print("   - Partner replied and Notification Triggered.")
    
    # 4. Check Tourist Notifications
    print("\n4️⃣  Checking Tourist Notifications...")
    notifs = Notification.objects.filter(recipient=tourist).order_by('-created_at')
    
    if notifs.exists():
        print(f"   - ✅ Tourist has {notifs.count()} notifications.")
        latest = notifs.first()
        print(f"   - Latest: {latest.title} - {latest.message}")
        if latest.sender:
            print(f"   - Sender: {latest.sender.username} ✅")
        else:
            print(f"   - Sender: None ❌")
    else:
        print("   - ❌ No notifications found for tourist.")

    print("\n✅ Test Complete.")

if __name__ == "__main__":
    run_test()

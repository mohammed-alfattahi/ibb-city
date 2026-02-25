
import os
import django
from django.contrib.auth import get_user_model
from django.conf import settings
from places.models import Establishment
from interactions.models import Notification, Review, PlaceComment
from management.models import PendingChange
from users.models import PartnerProfile, Role
from interactions.notifications.notification_service import NotificationService

User = get_user_model()

def run_test():
    print("🚀 Starting 360° Notification Verification (Admin, Partner, Tourist)...\n")
    
    # 1. Setup Users
    print("1️⃣  Setup Users & Roles...")
    admin, _ = User.objects.get_or_create(username='admin_test', defaults={'email': 'admin@test.com', 'is_staff': True, 'is_superuser': True})
    partner, _ = User.objects.get_or_create(username='partner_notif_test', defaults={'email': 'partner_n@test.com'})
    tourist, _ = User.objects.get_or_create(username='tourist_notif_test', defaults={'email': 'tourist_n@test.com'})
    
    # Ensure Partner Role
    partner_role, _ = Role.objects.get_or_create(name='Partner')
    partner.role = partner_role
    partner.save()
    
    # Clear previous notifications for clean test
    Notification.objects.filter(recipient__in=[admin, partner, tourist]).delete()
    print("   - Users ready. Old notifications cleared.")

    # =========================================================================
    # Scenario A: Admin Notifications (New Partner Request)
    # =========================================================================
    print("\n🅰️  Testing ADMIN Notifications...")
    
    # Simulate Logic: New Partner Registration triggers Admin Notification
    # We call NotificationService manually to simulate the signal/service call
    
    NotificationService.emit_event(
        event_name='STAFF_ALERT',
        payload={
            'title': 'تسجيل شريك جديد',
            'message': f"قام {partner.username} بالتسجيل كشريك.",
            'action_url': f'/admin/users/partnerprofile/{partner.id}/'
        },
        audience_criteria={'role': 'staff'},
        sender=partner
    )
    
    # Check Admin Inbox
    admin_notifs = Notification.objects.filter(recipient=admin).order_by('-created_at')
    if admin_notifs.exists():
        n = admin_notifs.first()
        print(f"   - ✅ Admin received: '{n.title}' from '{n.sender.username if n.sender else 'System'}'")
        print(f"   -    Message: {n.message}")
        print(f"   -    Link: {n.action_url}")
    else:
        print("   - ❌ Admin received NO notification.")

    # =========================================================================
    # Scenario B: Partner Notifications (Establishment Approval & New Review)
    # =========================================================================
    print("\n🅱️  Testing PARTNER Notifications...")
    
    place, _ = Establishment.objects.get_or_create(
        name='Partner Notif Cafe', 
        defaults={'owner': partner, 'category_id': 1}
    )
    
    # 1. Establishment Approved
    NotificationService.emit_event(
        event_name='ESTABLISHMENT_APPROVED',
        payload={
            'place_name': place.name,
            'action_url': f'/partner/establishments/{place.id}/'
        },
        audience_criteria={'user_id': partner.id},
        sender=admin
    )
    
    # 2. New Review from Tourist
    review, _ = Review.objects.get_or_create(
        user=tourist, place=place, 
        defaults={'rating': 4, 'comment': 'Nice place!'}
    )
    
    NotificationService.emit_event(
        event_name='NEW_REVIEW',
        payload={
            'place_name': place.name,
            'rating': review.rating,
            'action_url': f'/partner/reviews/{review.id}/'
        },
        audience_criteria={'user_id': partner.id},
        sender=tourist
    )
    
    # Check Partner Inbox
    partner_notifs = Notification.objects.filter(recipient=partner).order_by('-created_at')
    print(f"   - Partner has {partner_notifs.count()} notifications.")
    
    for n in partner_notifs:
        print(f"   - ✅ Partner received: '{n.title}' (Type: {n.notification_type})")
        print(f"   -    Sender: {n.sender.username if n.sender else 'System'}")

    # =========================================================================
    # Scenario C: Tourist Notifications (Reply to Review)
    # =========================================================================
    print("\n©️  Testing TOURIST Notifications...")
    
    # Partner replies
    NotificationService.emit_event(
        event_name='NEW_COMMENT_REPLY', # Or REVIEW_REPLY
        payload={
            'place_name': place.name,
            'replier': partner.username,
            'action_url': f'/places/{place.id}/'
        },
        audience_criteria={'user_id': tourist.id},
        sender=partner
    )
    
    tourist_notifs = Notification.objects.filter(recipient=tourist).order_by('-created_at')
    if tourist_notifs.exists():
        n = tourist_notifs.first()
        print(f"   - ✅ Tourist received: '{n.title}'")
        print(f"   -    Sender: {n.sender.username if n.sender else 'System'}")
    else:
        print("   - ❌ Tourist received NO notification.")

    print("\n✅ Verification Complete.")

    # =========================================================================
    # Scenario D: Verify Template Context (Partner Layout)
    # =========================================================================
    print("\n🇩  Testing Partner Notification Template Context...")
    from django.test import RequestFactory
    from interactions.views_public import NotificationListView
    
    factory = RequestFactory()
    request = factory.get('/notifications/')
    request.user = partner
    
    view = NotificationListView()
    view.setup(request) # Initialize view (sets request, args, kwargs)
    view.object_list = Notification.objects.none() # Mock empty queryset for ListView
    context = view.get_context_data()
    
    if context.get('base_template') == 'partners/base_partner.html':
        print(f"   - ✅ Correct base template for Partner: {context['base_template']}")
    else:
        print(f"   - ❌ Incorrect base template: {context.get('base_template')}")

    # Test Non-Partner (Tourist)
    request.user = tourist
    view = NotificationListView()
    view.setup(request)
    view.object_list = Notification.objects.none()
    context = view.get_context_data()
    if context.get('base_template') == 'base.html':
        print(f"   - ✅ Correct base template for Tourist: {context['base_template']}")
    else:
        print(f"   - ❌ Incorrect base template: {context.get('base_template')}")



if __name__ == "__main__":
    run_test()

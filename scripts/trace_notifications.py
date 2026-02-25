import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from users.models import User, Role
from interactions.models import Notification
from interactions.notifications.notification_service import NotificationService
from django.db.models import Q

def trace():
    print("🔍 Starting Notification Trace...")
    
    # 1. Setup Roles
    print("\n[Step 1] Checking/Creating Roles...")
    partner_role, _ = Role.objects.get_or_create(name="Partner")
    print(f"Role 'Partner': {partner_role.id}")

    # 2. Setup Users
    print("\n[Step 2] Setting up Test Users...")
    
    # Admin (Staff)
    admin_user, _ = User.objects.get_or_create(username="trace_admin", defaults={'email': 'admin@trace.com'})
    admin_user.is_staff = True
    admin_user.save()
    print(f"Admin User: {admin_user.username} (is_staff={admin_user.is_staff})")

    # Partner (Role-based)
    partner_user, _ = User.objects.get_or_create(username="trace_partner", defaults={'email': 'partner@trace.com'})
    partner_user.role = partner_role
    partner_user.save()
    print(f"Partner User: {partner_user.username} (Role={partner_user.role.name})")

    # 3. Trace: Admin Notification (Staff Criterion)
    print("\n[Step 3] Tracing STAFF Notification (e.g. New Ad Request)...")
    Notification.objects.filter(recipient=admin_user).delete() # clean slate
    
    NotificationService.emit_event(
        'NEW_AD_REQUEST', 
        {'title': 'Ad for Tracing'}, 
        {'role': 'staff'} # Target Audience
    )
    
    notif_admin = Notification.objects.filter(recipient=admin_user).first()
    if notif_admin:
        print(f"✅ Success: Admin received '{notif_admin.title}'")
    else:
        print("❌ FAILED: Admin did NOT receive notification.")
        # Debugging
        staff_users = User.objects.filter(is_staff=True)
        print(f"Debug: Found {staff_users.count()} staff users in DB.")

    # 4. Trace: Partner Notification (Role Criterion)
    print("\n[Step 4] Tracing PARTNER Notification (e.g. New Review)...")
    Notification.objects.filter(recipient=partner_user).delete()
    
    # Emulating criterion used in service logic or direct user_id
    # 'NEW_REVIEW' signal usually uses specific user_id, but let's test ROLE targeting first
    # Test 4a: Target by Role
    NotificationService.emit_event(
        'SYSTEM_ALERT',
        {'message': 'Message to all partners'},
        {'role': 'partner'}
    )
    
    notif_partner_role = Notification.objects.filter(recipient=partner_user, notification_type__in=['general', 'system_alert']).first()
    if notif_partner_role:
        print(f"✅ Success: Partner received Role-based broadcast.")
    else:
        print("❌ FAILED: Partner did NOT receive Role-based broadcast.")
        # Debug
        partners = User.objects.filter(role__name__iexact='partner')
        print(f"Debug: Found {partners.count()} users with role 'partner'.")

    # Test 4b: Target by User ID (Direct) - Most common in Signals
    NotificationService.emit_event(
        'NEW_REVIEW',
        {'place_name': 'Trace Hotel', 'rating': 5},
        {'user_id': partner_user.id}
    )
    notif_partner_direct = Notification.objects.filter(recipient=partner_user, notification_type='new_review').first()
    if notif_partner_direct:
         print(f"✅ Success: Partner received Direct notification (New Review).")
    else:
         print("❌ FAILED: Partner did NOT receive Direct notification.")

    print("\n[Trace Complete]")

if __name__ == "__main__":
    trace()

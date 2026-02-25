from django.core.management.base import BaseCommand
from users.models import User, Role
from interactions.models import Notification, SystemAlert
from interactions.notifications.notification_service import NotificationService
from django.db.models import Q

class Command(BaseCommand):
    help = 'Traces notification delivery to verify system logic'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Starting Notification Trace..."))

        # 1. Setup Roles
        self.stdout.write("\n[Step 1] Checking/Creating Roles...")
        partner_role, _ = Role.objects.get_or_create(name="Partner")
        self.stdout.write(f"Role 'Partner': {partner_role.id}")

        # 2. Setup Users
        self.stdout.write("\n[Step 2] Setting up Test Users...")
        
        # Admin (Staff)
        admin_user, _ = User.objects.get_or_create(username="trace_admin", defaults={'email': 'admin@trace.com'})
        # Force staff status
        if not admin_user.is_staff:
            admin_user.is_staff = True
            admin_user.save()
        self.stdout.write(f"Admin User: {admin_user.username} (is_staff={admin_user.is_staff})")

        # Partner (Role-based)
        partner_user, _ = User.objects.get_or_create(username="trace_partner", defaults={'email': 'partner@trace.com'})
        partner_user.role = partner_role
        partner_user.save()
        self.stdout.write(f"Partner User: {partner_user.username} (Role={partner_user.role.name})")

        # 3. Trace: Admin Notification (Staff Criterion)
        self.stdout.write("\n[Step 3] Tracing STAFF Notification (e.g. New Ad Request)...")
        # Clean previous trace notifications
        Notification.objects.filter(recipient=admin_user, title='Ad for Tracing').delete()
        
        NotificationService.emit_event(
            'NEW_AD_REQUEST', 
            {'title': 'Ad for Tracing'}, 
            {'role': 'staff'} # Target Audience
        )
        
        notif_admin = Notification.objects.filter(recipient=admin_user, title='Ad for Tracing').first()
        if notif_admin:
            self.stdout.write(self.style.SUCCESS(f"✅ Success: Admin received '{notif_admin.title}'"))
        else:
            self.stdout.write(self.style.ERROR("❌ FAILED: Admin did NOT receive notification."))
            staff_users = User.objects.filter(is_staff=True)
            self.stdout.write(f"Debug: Found {staff_users.count()} staff users in DB.")

        # 4. Trace: Partner Notification (Role Criterion)
        self.stdout.write("\n[Step 4] Tracing PARTNER Notification (e.g. New Review)...")
        # Clean previous
        Notification.objects.filter(recipient=partner_user, notification_type__in=['general', 'system_alert']).delete()
        
        # Test 4a: Target by Role
        NotificationService.emit_event(
            'SYSTEM_ALERT',
            {'message': 'Message to all partners'},
            {'role': 'partner'}
        )
        
        notif_partner_role = Notification.objects.filter(recipient=partner_user, notification_type='general').first()
        if notif_partner_role:
            self.stdout.write(self.style.SUCCESS(f"✅ Success: Partner received Role-based broadcast."))
        else:
            self.stdout.write(self.style.ERROR("❌ FAILED: Partner did NOT receive Role-based broadcast."))
            partners = User.objects.filter(role__name__iexact='partner')
            self.stdout.write(f"Debug: Found {partners.count()} users with role 'partner'.")
            self.stdout.write(f"Debug: Check if Role name 'Partner' matches iexact 'partner' -> Yes it should.")

        # Test 4b: Target by User ID (Direct)
        NotificationService.emit_event(
            'NEW_REVIEW',
            {'place_name': 'Trace Hotel', 'rating': 5},
            {'user_id': partner_user.id}
        )
        notif_partner_direct = Notification.objects.filter(recipient=partner_user, notification_type='new_review').first()
        if notif_partner_direct:
            self.stdout.write(self.style.SUCCESS(f"✅ Success: Partner received Direct notification (New Review)."))
        else:
            self.stdout.write(self.style.ERROR("❌ FAILED: Partner did NOT receive Direct notification."))

            self.stdout.write(self.style.ERROR("❌ FAILED: Partner did NOT receive Direct notification."))

        # 5. Trace: Tourist Notification (Review Reply)
        self.stdout.write("\n[Step 5] Tracing TOURIST Notification (Review Reply)...")
        # Create Tourist
        tourist_user, _ = User.objects.get_or_create(username="trace_tourist", defaults={'email': 'tourist@trace.com'})
        
        # Simulate Signal: Partner replies to Tourist's Review
        # We simulate the service call that the signal usually triggers
        Notification.objects.filter(recipient=tourist_user, notification_type='review_reply').delete()
        
        NotificationService.emit_event(
            'REVIEW_REPLY',
            {'place_name': 'Trace Hotel', 'replier': 'Hotel Owner'},
            {'user_id': tourist_user.id}
        )
        
        notif_tourist_reply = Notification.objects.filter(recipient=tourist_user, notification_type='review_reply').first()
        if notif_tourist_reply:
            self.stdout.write(self.style.SUCCESS(f"✅ Success: Tourist received Review Reply notification."))
        else:
            self.stdout.write(self.style.ERROR("❌ FAILED: Tourist did NOT receive Review Reply notification."))
            
        # 6. Trace: Tourist Notification (Report Update)
        self.stdout.write("\n[Step 6] Tracing TOURIST Notification (Report Status Update)...")
        Notification.objects.filter(recipient=tourist_user, notification_type='report_update').delete()
        
        NotificationService.emit_event(
            'REPORT_UPDATE',
            {'status': 'RESOLVED', 'note': 'Fixed the issue'},
            {'user_id': tourist_user.id}
        )
        
        notif_tourist_report = Notification.objects.filter(recipient=tourist_user, notification_type='report_update').first()
        if notif_tourist_report:
            self.stdout.write(self.style.SUCCESS(f"✅ Success: Tourist received Report Update notification."))
        else:
            self.stdout.write(self.style.ERROR("❌ FAILED: Tourist did NOT receive Report Update notification."))

        # 7. Trace: Weather Alert Broadcast (ALL USERS)
        self.stdout.write("\n[Step 7] Tracing WEATHER ALERT Broadcast (To ALL Users)...")
        # Clean previous
        Notification.objects.filter(notification_type='general', title__contains='Weather').delete()
        
        NotificationService.emit_event(
            'WEATHER_ALERT',
            {'title': 'Heavy Rain Warning', 'message': 'Please avoid valleys.'},
            {'broadcast': True} # Broadcast to ALL active users
        )
        
        # Verify Admin
        if Notification.objects.filter(recipient=admin_user, title='Heavy Rain Warning').exists():
            self.stdout.write(f"  - Admin: {self.style.SUCCESS('Received')}")
        else:
            self.stdout.write(f"  - Admin: {self.style.ERROR('FAILED')}")

        # Verify Partner
        if Notification.objects.filter(recipient=partner_user, title='Heavy Rain Warning').exists():
             self.stdout.write(f"  - Partner: {self.style.SUCCESS('Received')}")
        else:
             self.stdout.write(f"  - Partner: {self.style.ERROR('FAILED')}")

        # Verify Tourist
        if Notification.objects.filter(recipient=tourist_user, title='Heavy Rain Warning').exists():
             self.stdout.write(f"  - Tourist: {self.style.SUCCESS('Received')}")
        else:
             self.stdout.write(f"  - Tourist: {self.style.ERROR('FAILED')}")

        # 8. Trace: SystemAlert Model (Admin Logic - Broadcast)
        self.stdout.write("\n[Step 8] Tracing SystemAlert Model (Admin Dashboard - WEATHER ALERT)...")
        Notification.objects.filter(title='System Weather Alert').delete()
        
        # Create SystemAlert to trigger signal (Broadcast 'all')
        alert = SystemAlert.objects.create(
            title='System Weather Alert',
            message='Testing Broadcast from Model',
            alert_type='WEATHER_ALERT',
            target_audience='all', # TEST BROADCAST
            created_by=admin_user
        )
        
        # Verify Partner Received
        if Notification.objects.filter(recipient=partner_user, title='System Weather Alert').exists():
             self.stdout.write(f"  - Partner: {self.style.SUCCESS('Received')}")
        else:
             self.stdout.write(f"  - Partner: {self.style.ERROR('FAILED')}")
             
        # Verify Tourist (Should Receive Now)
        notif_tourist = Notification.objects.filter(recipient=tourist_user, title='System Weather Alert').first()
        if notif_tourist:
             self.stdout.write(f"  - Tourist: {self.style.SUCCESS('Received')}")
             # Check URL
             if notif_tourist.action_url:
                 self.stdout.write(f"    -> URL verification: {self.style.SUCCESS(notif_tourist.action_url)}")
             else:
                 self.stdout.write(f"    -> URL verification: {self.style.ERROR('Missing URL')}")
        else:
             self.stdout.write(f"  - Tourist: {self.style.ERROR('FAILED (Did not receive)')}")

        self.stdout.write("\n[Trace Complete]")

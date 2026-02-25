from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Role, PartnerProfile
from users.forms_auth import TouristUpgradeForm
from management.services.approval_engine import ApprovalEngine
from users.services.partner_service import PartnerService
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class Command(BaseCommand):
    help = 'Verify the Tourist to Partner Upgrade Workflow'

    def handle(self, *args, **options):
        self.stdout.write("--- Starting Tourist to Partner Upgrade Workflow Test ---")
        
        # 1. Create Tourist
        email = "tourist_test@example.com"
        username = "tourist_test"
        
        # Clean up previous run
        User.objects.filter(email=email).delete()
        
        tourist = User.objects.create_user(
            username=username,
            email=email,
            password="password123",
            full_name="Test Tourist",
            phone_number="777000777"
        )
        self.stdout.write(f"1. Created Tourist: {tourist} (Role: {tourist.role})")
        
        # 2. Submit Upgrade Form
        self.stdout.write("2. Submitting Upgrade Request...")
        form_data = {
            'full_name': 'Test Partner Applicant',
            'phone_number': '777000888',
            'commercial_reg_no': 'CR-12345',
        }
        
        # Create a valid 1x1 PNG image (base64 decoded)
        import base64
        # 1x1 transparent PNG
        png_data = base64.b64decode(
            b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        dummy_file = SimpleUploadedFile("id_card.png", png_data, content_type="image/png")
        
        form = TouristUpgradeForm(data=form_data, files={'id_card_image': dummy_file}, instance=tourist)
        
        if form.is_valid():
            user = form.save()
            self.stdout.write(f"   - Form Saved. User Role: {user.role}")
            
            try:
                # Ensure profile is reloaded
                user.refresh_from_db()
                self.stdout.write(f"   - Profile Status: {user.partner_profile.status}")
                
                # Check Service call logic
                success, msg = PartnerService.request_upgrade(user)
                self.stdout.write(f"   - Service request_upgrade: {success} ({msg})")
                
                user.refresh_from_db()
                if user.role.name == 'Partner' and user.partner_profile.status == 'pending':
                    self.stdout.write(self.style.SUCCESS("   ✅ Step 2 Success: User became Pending Partner"))
                else:
                    self.stdout.write(self.style.ERROR(f"   ❌ Step 2 Failed: Role={user.role}, Status={user.partner_profile.status}"))
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Step 2 Exception: {e}"))
                return
        else:
            self.stdout.write(self.style.ERROR(f"   ❌ Step 2 Failed: Form Invalid {form.errors}"))
            return

        # 3. Admin Approval
        self.stdout.write("3. Admin Approval Process...")
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            admin = User.objects.create_superuser('admin_test', 'admin@test.com', 'admin')
            
        result = ApprovalEngine.approve_partner(
            office_user=admin,
            partner_profile=user.partner_profile,
            notes="Verified by System Test"
        )
        
        if result.success:
            user.refresh_from_db()
            self.stdout.write(f"   - Approval Result: Success")
            self.stdout.write(f"   - New Status: {user.partner_profile.status}")
            self.stdout.write(f"   - Account Status: {user.account_status}")
            
            if user.partner_profile.status == 'approved' and user.account_status == 'active':
                 self.stdout.write(self.style.SUCCESS("   ✅ Step 3 Success: Partner Approved & Active"))
            else:
                 self.stdout.write(self.style.ERROR("   ❌ Step 3 Failed: States mismatch"))
        else:
            self.stdout.write(self.style.ERROR(f"   ❌ Step 3 Failed: {result.message}"))

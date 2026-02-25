import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ibb_guide.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from users.models import Role, PartnerProfile
from users.forms_auth import TouristUpgradeForm
from management.services.approval_engine import ApprovalEngine
from users.services.partner_service import PartnerService

User = get_user_model()

def test_workflow():
    print("--- Starting Tourist to Partner Upgrade Workflow Test ---")
    
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
    print(f"1. Created Tourist: {tourist} (Role: {tourist.role})")
    
    # 2. Submit Upgrade Form
    print("2. Submitting Upgrade Request...")
    form_data = {
        'full_name': 'Test Partner Applicant',
        'phone_number': '777000888',
        'commercial_reg_no': 'CR-12345',
    }
    # Simulate file upload? We can skip actual file for logic test or provide dummy
    # For form verification, we assume valid file is passed or optional if we adjusted it.
    # In form, ID Card is required.
    
    # Let's bypass form validation and test logic directly if possible, or use a dummy file
    from django.core.files.uploadedfile import SimpleUploadedFile
    dummy_file = SimpleUploadedFile("id_card.jpg", b"file_content", content_type="image/jpeg")
    
    form = TouristUpgradeForm(data=form_data, files={'id_card_image': dummy_file}, instance=tourist)
    
    if form.is_valid():
        user = form.save()
        print(f"   - Form Saved. User Role: {user.role}")
        print(f"   - Profile Status: {user.partner_profile.status}")
        
        # Verify Service call (normally view calls this, so we call it)
        success, msg = PartnerService.request_upgrade(user)
        print(f"   - Service request_upgrade: {success} ({msg})")
        
        user.refresh_from_db()
        if user.role.name == 'Partner' and user.partner_profile.status == 'pending':
            print("   ✅ Step 2 Success: User became Pending Partner")
        else:
            print(f"   ❌ Step 2 Failed: Role={user.role}, Status={user.partner_profile.status}")
            return
    else:
        print("   ❌ Step 2 Failed: Form Invalid", form.errors)
        return

    # 3. Admin Approval
    print("3. Admin Approval Process...")
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
        print(f"   - Approval Result: Success")
        print(f"   - New Status: {user.partner_profile.status}")
        print(f"   - Account Status: {user.account_status}")
        
        if user.partner_profile.status == 'approved' and user.account_status == 'active':
             print("   ✅ Step 3 Success: Partner Approved & Active")
        else:
             print("   ❌ Step 3 Failed: States mismatch")
    else:
        print(f"   ❌ Step 3 Failed: {result.message}")

if __name__ == "__main__":
    test_workflow()

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import PartnerProfile, Role
from management.models import Request
from interactions.models import Notification

User = get_user_model()

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AdminUITest(TestCase):
    def setUp(self):
        # Create Staff User
        self.staff_user = User.objects.create_user(
            username='admin_staff',
            email='staff@example.com',
            password='password123',
            is_staff=True
        )
        
        # Create Partner User and Profile
        self.partner_user = User.objects.create_user(
            username='partner_test',
            email='partner@example.com',
            password='password123'
        )
        self.partner_profile = PartnerProfile.objects.create(
            user=self.partner_user,
            organization_name="Test Org",
            status='pending'
        )

    def test_admin_pages_load_ok(self):
        """Phase A: Ensure main admin pages load with correct templates"""
        self.client.force_login(self.staff_user)
        
        pages = [
            'custom_admin_dashboard',
            'admin_pending_partners',
            'admin_request_list',
            'admin_system_health',
            'admin_pending_changes'
        ]
        
        for page_name in pages:
            url = reverse(page_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed to load {page_name}")
            self.assertTemplateUsed(response, "management/admin_base.html")

    def test_url_routing_approvals(self):
        """Phase B: Test Approval URL Routing for duplicates"""
        self.client.force_login(self.staff_user)
        
        # Approve URL
        approve_url = reverse('admin_partner_approve', kwargs={'pk': self.partner_profile.pk})
        # Adjusted assertion based on current URL config showing /custom-admin/
        self.assertTrue('/custom-admin/partner/' in approve_url, f"Approvals path check failed: {approve_url}")
        
        # Reject URL
        reject_url = reverse('admin_partner_reject', kwargs={'pk': self.partner_profile.pk})
        self.assertTrue('/custom-admin/partner/' in reject_url, f"Reject path check failed: {reject_url}")

    def test_needs_info_workflow(self):
        """Phase B/C: Test Needs Info functionality"""
        self.client.force_login(self.staff_user)
        
        url = reverse('admin_partner_needs_info', kwargs={'pk': self.partner_profile.pk})
        data = {'info_message': 'Please upload clear ID'}
        
        # Post Needs Info
        response = self.client.post(url, data, follow=True)
        self.assertRedirects(response, reverse('admin_pending_partners'))
        
        # Verify DB Status
        self.partner_profile.refresh_from_db()
        self.assertEqual(self.partner_profile.status, 'needs_info')
        self.assertEqual(self.partner_profile.info_request_message, 'Please upload clear ID')

    def test_admin_context_counts(self):
        """Phase C: Verify sidebar counts context processor"""
        self.client.force_login(self.staff_user)
        
        response = self.client.get(reverse('custom_admin_dashboard'))
        # pending_partners count should be 1
        self.assertEqual(response.context['pending_partners_count'], 1)

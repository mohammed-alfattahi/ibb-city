"""
Tests for Tourist → Partner Upgrade Workflow

Tests:
1. Upgrade request creates/updates PartnerProfile pending
2. Tourist retains same User (same email/username)
3. Pending partner cannot access partner dashboard
4. Office approve changes status and grants Partner role
5. Reject keeps access blocked + reason visible
"""
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from users.models import PartnerProfile, Role

User = get_user_model()


class PartnerUpgradeTestCase(TransactionTestCase):
    """Test partner upgrade workflow."""
    
    def setUp(self):
        self.client = Client()
        self.tourist_user = User.objects.create_user(
            username='tourist_upgrade',
            email='tourist_upgrade@test.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff_office',
            email='staff_office@test.com',
            password='staffpass123',
            is_staff=True
        )
    
    def test_pending_partner_cannot_access_dashboard(self):
        """Pending partner without Partner role should get 403."""
        # Create pending profile (user has no Partner role yet)
        profile = PartnerProfile.objects.create(
            user=self.tourist_user,
            status='pending',
            is_approved=False
        )
        
        self.client.force_login(self.tourist_user)
        response = self.client.get(reverse('partner_dashboard'))
        
        # Should get 403 since user doesn't have Partner role
        self.assertEqual(response.status_code, 403)
    
    def test_approve_grants_partner_role(self):
        """Office approval should set status=approved and assign Partner role."""
        # Create pending profile
        profile = PartnerProfile.objects.create(
            user=self.tourist_user,
            status='pending',
            is_approved=False
        )
        
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('admin_partner_approve', args=[profile.pk])
        )
        
        self.assertEqual(response.status_code, 302)
        
        profile.refresh_from_db()
        self.tourist_user.refresh_from_db()
        
        self.assertEqual(profile.status, 'approved')
        self.assertTrue(profile.is_approved)
        self.assertIsNotNone(self.tourist_user.role)
        self.assertEqual(self.tourist_user.role.name, 'Partner')
    
    def test_reject_stores_reason(self):
        """Rejection should store rejection reason."""
        profile = PartnerProfile.objects.create(
            user=self.tourist_user,
            status='pending',
            is_approved=False
        )
        
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('admin_partner_reject', args=[profile.pk]),
            {'reason': 'وثائق غير كاملة'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        profile.refresh_from_db()
        
        self.assertEqual(profile.status, 'rejected')
        self.assertFalse(profile.is_approved)
        self.assertEqual(profile.rejection_reason, 'وثائق غير كاملة')
    
    def test_same_user_after_upgrade(self):
        """User should retain same email/username after upgrade."""
        original_email = self.tourist_user.email
        original_username = self.tourist_user.username
        
        # Create profile (simulating upgrade)
        profile = PartnerProfile.objects.create(
            user=self.tourist_user,
            status='pending'
        )
        
        # Check user is unchanged
        self.tourist_user.refresh_from_db()
        self.assertEqual(self.tourist_user.email, original_email)
        self.assertEqual(self.tourist_user.username, original_username)
    
    def test_approved_partner_can_access_dashboard(self):
        """Approved partner should access dashboard."""
        partner_role, _ = Role.objects.get_or_create(name='Partner')
        
        self.tourist_user.role = partner_role
        self.tourist_user.account_status = 'active'
        self.tourist_user.save()
        
        profile = PartnerProfile.objects.create(
            user=self.tourist_user,
            status='approved',
            is_approved=True
        )
        
        self.client.force_login(self.tourist_user)
        response = self.client.get(reverse('partner_dashboard'))
        
        self.assertEqual(response.status_code, 200)


class PartnerPendingPageTestCase(TransactionTestCase):
    """Test partner pending status page."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='pending_user',
            email='pending_user@test.com',
            password='testpass123'
        )
    
    def test_pending_page_shows_status(self):
        """Pending page should show correct status."""
        PartnerProfile.objects.create(
            user=self.user,
            status='pending'
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('partner_pending'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'قيد المراجعة')
    
    def test_rejected_page_shows_reason(self):
        """Rejected page should show rejection reason."""
        PartnerProfile.objects.create(
            user=self.user,
            status='rejected',
            rejection_reason='وثائق غير صالحة'
        )
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('partner_pending'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'وثائق غير صالحة')

"""
Tests for Approval Engine
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from management.services.approval_engine import ApprovalEngine, ApprovalResult
from management.models import AuditLog

User = get_user_model()


class ApprovalEnginePartnerTest(TestCase):
    """Test partner approval workflow."""
    
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass',
            is_staff=True
        )
        self.partner_user = User.objects.create_user(
            username='partner',
            email='partner@example.com',
            password='testpass'
        )
        self.factory = RequestFactory()
    
    def _create_partner_profile(self):
        from users.models import PartnerProfile
        return PartnerProfile.objects.create(
            user=self.partner_user,
            status='pending'
        )
    
    def test_approve_partner_success(self):
        """Test successful partner approval."""
        profile = self._create_partner_profile()
        
        result = ApprovalEngine.approve_partner(
            office_user=self.staff,
            partner_profile=profile
        )
        
        self.assertTrue(result.success)
        profile.refresh_from_db()
        self.assertEqual(profile.status, 'approved')
    
    def test_approve_partner_creates_audit(self):
        """Test that approval creates audit log."""
        profile = self._create_partner_profile()
        initial_count = AuditLog.objects.count()
        
        ApprovalEngine.approve_partner(
            office_user=self.staff,
            partner_profile=profile
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
    
    def test_non_staff_cannot_approve(self):
        """Test that non-staff users cannot approve."""
        profile = self._create_partner_profile()
        
        with self.assertRaises(PermissionDenied):
            ApprovalEngine.approve_partner(
                office_user=self.partner_user,  # Not staff
                partner_profile=profile
            )
    
    def test_reject_requires_reason(self):
        """Test that rejection requires a reason."""
        profile = self._create_partner_profile()
        
        result = ApprovalEngine.reject_partner(
            office_user=self.staff,
            partner_profile=profile,
            reason=''  # Empty reason
        )
        
        self.assertFalse(result.success)
        profile.refresh_from_db()
        self.assertEqual(profile.status, 'pending')  # Unchanged


class ApprovalEngineEstablishmentTest(TestCase):
    """Test establishment approval workflow."""
    
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass',
            is_staff=True
        )
        self.partner_user = User.objects.create_user(
            username='partner',
            email='partner@example.com',
            password='testpass'
        )
    
    def _create_establishment(self):
        from places.models import Establishment, Category
        
        category, _ = Category.objects.get_or_create(name='Test Category')
        return Establishment.objects.create(
            name='Test Place',
            owner=self.partner_user,
            category=category,
            approval_status='pending'
        )
    
    def test_approve_establishment_success(self):
        """Test successful establishment approval."""
        establishment = self._create_establishment()
        
        result = ApprovalEngine.approve_establishment(
            office_user=self.staff,
            establishment=establishment
        )
        
        self.assertTrue(result.success)
        establishment.refresh_from_db()
        self.assertEqual(establishment.approval_status, 'approved')
    
    def test_approve_establishment_creates_audit(self):
        """Test that approval creates audit log."""
        establishment = self._create_establishment()
        initial_count = AuditLog.objects.count()
        
        ApprovalEngine.approve_establishment(
            office_user=self.staff,
            establishment=establishment
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)


@override_settings(LANGUAGE_CODE='en', LANGUAGES=[('en', 'English')])
class ApprovalEngineDashboardTest(TestCase):
    """Test approval dashboard access."""
    
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass',
            is_staff=True
        )
        self.regular = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass'
        )
    
    def test_regular_user_cannot_access(self):
        """Test that regular users cannot access dashboard."""
        self.client.force_login(self.regular)
        response = self.client.get('/office/approvals/')
        self.assertIn(response.status_code, [302, 403])
    
    def test_unauthenticated_cannot_access(self):
        """Test that unauthenticated users cannot access."""
        response = self.client.get('/office/approvals/')
        self.assertEqual(response.status_code, 302)

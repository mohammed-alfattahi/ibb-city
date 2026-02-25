"""
Tests for Establishment Publishing & Approval Workflow

Tests cover:
1. New establishment is NOT visible in public views
2. Approved establishment appears publicly
3. Rejected establishment remains hidden
4. PublicEstablishmentManager filters correctly
5. Office user can approve/reject
6. Partner cannot approve their own establishment
"""
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from places.models import Establishment, Category
from places.views_public import get_public_places_queryset
from users.models import PartnerProfile, Role

User = get_user_model()


class EstablishmentApprovalModelTestCase(TransactionTestCase):
    """Test Establishment approval model methods."""
    
    def setUp(self):
        self.partner_role, _ = Role.objects.get_or_create(name='Partner')
        
        self.partner_user = User.objects.create_user(
            username='partner_approval',
            email='partner_approval@test.com',
            password='testpass123'
        )
        self.partner_user.role = self.partner_role
        self.partner_user.account_status = 'active'
        self.partner_user.save()
        
        PartnerProfile.objects.create(
            user=self.partner_user,
            is_approved=True
        )
        
        self.admin_user = User.objects.create_superuser(
            username='admin_approval',
            email='admin_approval@test.com',
            password='adminpass123'
        )
        
        self.category = Category.objects.create(name='Approval Test Category')
    
    def test_new_establishment_is_pending(self):
        """New establishment should have pending approval_status."""
        establishment = Establishment.objects.create(
            name='New Test Establishment',
            category=self.category,
            owner=self.partner_user,
            is_active=True
        )
        
        self.assertEqual(establishment.approval_status, 'pending')
    
    def test_pending_establishment_not_in_public_manager(self):
        """Pending establishment should NOT appear in public queryset."""
        establishment = Establishment.objects.create(
            name='Pending Establishment',
            category=self.category,
            owner=self.partner_user,
            approval_status='pending',
            is_active=True
        )
        
        # Should NOT be in public manager
        self.assertNotIn(establishment, Establishment.public.all())
        
        # Should be in regular objects
        self.assertIn(establishment, Establishment.objects.all())
    
    def test_approved_establishment_in_public_manager(self):
        """Approved establishment SHOULD appear in public queryset."""
        establishment = Establishment.objects.create(
            name='Approved Establishment',
            category=self.category,
            owner=self.partner_user,
            approval_status='approved',
            is_active=True
        )
        
        self.assertIn(establishment, Establishment.public.all())
    
    def test_rejected_establishment_not_in_public_manager(self):
        """Rejected establishment should NOT appear in public queryset."""
        establishment = Establishment.objects.create(
            name='Rejected Establishment',
            category=self.category,
            owner=self.partner_user,
            approval_status='rejected',
            rejected_reason='Not meeting standards',
            is_active=True
        )
        
        self.assertNotIn(establishment, Establishment.public.all())
    
    def test_approve_method_updates_status(self):
        """approve() method should update establishment correctly."""
        establishment = Establishment.objects.create(
            name='To Be Approved',
            category=self.category,
            owner=self.partner_user,
            approval_status='pending',
            is_active=True
        )
        
        success, message = establishment.approve(self.admin_user)
        
        self.assertTrue(success)
        establishment.refresh_from_db()
        self.assertEqual(establishment.approval_status, 'approved')
        self.assertEqual(establishment.approved_by, self.admin_user)
        self.assertIsNotNone(establishment.approved_at)
    
    def test_reject_method_updates_status(self):
        """reject() method should update establishment with reason."""
        establishment = Establishment.objects.create(
            name='To Be Rejected',
            category=self.category,
            owner=self.partner_user,
            approval_status='pending',
            is_active=True
        )
        
        success, message = establishment.reject(self.admin_user, 'Missing license')
        
        self.assertTrue(success)
        establishment.refresh_from_db()
        self.assertEqual(establishment.approval_status, 'rejected')
        self.assertEqual(establishment.rejected_reason, 'Missing license')


class PublicVisibilityTestCase(TransactionTestCase):
    """Test that public views correctly filter unapproved establishments."""
    
    def setUp(self):
        self.partner_role, _ = Role.objects.get_or_create(name='Partner')
        
        self.partner_user = User.objects.create_user(
            username='partner_vis',
            email='partner_vis@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Visibility Test Category')
        
        # Create approved establishment
        self.approved_est = Establishment.objects.create(
            name='Approved Visible',
            category=self.category,
            owner=self.partner_user,
            approval_status='approved',
            is_active=True
        )
        
        # Create pending establishment
        self.pending_est = Establishment.objects.create(
            name='Pending Hidden',
            category=self.category,
            owner=self.partner_user,
            approval_status='pending',
            is_active=True
        )
        
        self.client = Client()
    
    def test_get_public_places_queryset_filters_correctly(self):
        """get_public_places_queryset should exclude unapproved."""
        public_places = get_public_places_queryset()
        
        # Convert to list of IDs
        public_ids = list(public_places.values_list('id', flat=True))
        
        # Approved should be included (via place_ptr_id)
        self.assertIn(self.approved_est.place_ptr_id, public_ids)
        
        # Pending should be excluded
        self.assertNotIn(self.pending_est.place_ptr_id, public_ids)


class OfficeApprovalAccessTestCase(TransactionTestCase):
    """Test that only staff can access approval views."""
    
    def setUp(self):
        self.partner_role, _ = Role.objects.get_or_create(name='Partner')
        
        self.partner_user = User.objects.create_user(
            username='partner_access',
            email='partner_access@test.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff_access',
            email='staff_access@test.com',
            password='testpass123',
            is_staff=True
        )
        
        self.client = Client()
    
    def test_partner_cannot_access_approval_page(self):
        """Partner should not be able to access establishment approval page."""
        self.client.force_login(self.partner_user)
        
        response = self.client.get(reverse('admin_establishment_approval'))
        
        # Should be forbidden or redirect
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_can_access_approval_page(self):
        """Staff user should be able to access establishment approval page."""
        self.client.force_login(self.staff_user)
        
        response = self.client.get(reverse('admin_establishment_approval'))
        
        self.assertEqual(response.status_code, 200)

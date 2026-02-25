"""
Tests for Field-Level Approval System (PendingChange)

Tests cover:
1. Creating PendingChange does NOT update Establishment immediately
2. Approving PendingChange updates Establishment
3. Rejecting PendingChange keeps original values
4. Immediate changes create AuditLog entries
5. Immediate changes notify office staff
6. Unapproved partners cannot access partner dashboard
"""
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch

from management.models import PendingChange, AuditLog
from management.services.pending_change_service import PendingChangeService
from places.models import Establishment, Category
from places.services.partner_update_service import PartnerUpdateService
from interactions.models import Notification
from users.models import PartnerProfile

User = get_user_model()


class PendingChangeModelTestCase(TransactionTestCase):
    """Test PendingChange model creation and properties."""
    
    def setUp(self):
        # Create partner user
        self.partner_user = User.objects.create_user(
            username='partner_test',
            email='partner@test.com',
            password='testpass123'
        )
        PartnerProfile.objects.create(
            user=self.partner_user,
            is_approved=True,
            status='approved'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create category and establishment (no category_type field)
        self.category = Category.objects.create(name='Test Category')
        self.establishment = Establishment.objects.create(
            name='Original Name',
            description='Original Description',
            category=self.category,
            owner=self.partner_user,
            license_status='Approved',
            is_active=True
        )
    
    @patch('management.services.pending_change_service.PendingChangeService._notify_office_of_request')
    def test_pending_change_does_not_update_establishment(self, mock_notify):
        """Creating a PendingChange should NOT update the Establishment."""
        original_name = self.establishment.name
        
        # Request a name change
        success, message, pending_change = PendingChangeService.request_sensitive_change(
            user=self.partner_user,
            establishment=self.establishment,
            field_name='name',
            new_value='New Requested Name'
        )
        
        # Assert PendingChange was created
        self.assertTrue(success)
        self.assertIsNotNone(pending_change)
        self.assertEqual(pending_change.status, 'pending')
        self.assertEqual(pending_change.new_value, 'New Requested Name')
        
        # Refresh establishment from DB
        self.establishment.refresh_from_db()
        
        # Assert establishment name is UNCHANGED
        self.assertEqual(self.establishment.name, original_name)
    
    @patch('management.services.pending_change_service.PendingChangeService._notify_partner_of_decision')
    def test_approve_pending_change_updates_establishment(self, mock_notify):
        """Approving a PendingChange should update the Establishment."""
        # Create pending change
        pending_change = PendingChange.objects.create(
            establishment=self.establishment,
            field_name='name',
            old_value='Original Name',
            new_value='Approved New Name',
            requested_by=self.partner_user
        )
        
        # Approve the change
        success, message = PendingChangeService.approve_change(
            admin_user=self.admin_user,
            pending_change=pending_change
        )
        
        # Assert success
        self.assertTrue(success)
        
        # Refresh pending_change
        pending_change.refresh_from_db()
        self.assertEqual(pending_change.status, 'approved')
        self.assertEqual(pending_change.reviewed_by, self.admin_user)
        self.assertIsNotNone(pending_change.reviewed_at)
        
        # Refresh establishment from DB
        self.establishment.refresh_from_db()
        
        # Assert establishment name is NOW updated
        self.assertEqual(self.establishment.name, 'Approved New Name')
    
    @patch('management.services.pending_change_service.PendingChangeService._notify_partner_of_decision')
    def test_reject_pending_change_keeps_original_value(self, mock_notify):
        """Rejecting a PendingChange should keep the original Establishment value."""
        original_description = self.establishment.description
        
        # Create pending change for description
        pending_change = PendingChange.objects.create(
            establishment=self.establishment,
            field_name='description',
            old_value=original_description,
            new_value='This should NOT appear',
            requested_by=self.partner_user
        )
        
        # Reject the change
        success, message = PendingChangeService.reject_change(
            admin_user=self.admin_user,
            pending_change=pending_change,
            note='Not appropriate content'
        )
        
        # Assert success
        self.assertTrue(success)
        
        # Refresh pending_change
        pending_change.refresh_from_db()
        self.assertEqual(pending_change.status, 'rejected')
        self.assertEqual(pending_change.review_note, 'Not appropriate content')
        
        # Refresh establishment from DB
        self.establishment.refresh_from_db()
        
        # Assert description is UNCHANGED
        self.assertEqual(self.establishment.description, original_description)
    
    @patch('management.services.pending_change_service.PendingChangeService._notify_office_of_request')
    def test_audit_log_created_on_request(self, mock_notify):
        """Creating a PendingChange should create an AuditLog entry."""
        initial_audit_count = AuditLog.objects.count()
        
        PendingChangeService.request_sensitive_change(
            user=self.partner_user,
            establishment=self.establishment,
            field_name='name',
            new_value='Audit Test Name'
        )
        
        # Assert audit log was created
        self.assertEqual(AuditLog.objects.count(), initial_audit_count + 1)
        
        audit_log = AuditLog.objects.latest('created_at')
        self.assertEqual(audit_log.action, 'REQUEST_CHANGE')
        self.assertEqual(audit_log.user, self.partner_user)


class PartnerUpdateServiceTestCase(TransactionTestCase):
    """Test PartnerUpdateService for immediate changes."""
    
    def setUp(self):
        self.partner_user = User.objects.create_user(
            username='partner2',
            email='partner2@test.com',
            password='testpass123'
        )
        PartnerProfile.objects.create(
            user=self.partner_user,
            is_approved=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.category = Category.objects.create(name='Immediate Test Category')
        self.establishment = Establishment.objects.create(
            name='Immediate Test Establishment',
            category=self.category,
            owner=self.partner_user,
            license_status='Approved',
            is_active=True
        )
    
    @patch('places.services.partner_update_service.PartnerUpdateService._notify_office_of_update')
    def test_immediate_change_creates_audit_log(self, mock_notify):
        """Applying immediate change should create an AuditLog entry."""
        initial_count = AuditLog.objects.count()
        
        PartnerUpdateService.apply_immediate_change(
            user=self.partner_user,
            establishment=self.establishment,
            field_name='working_hours',
            old_value={'saturday': 'closed'},
            new_value={'saturday': '9:00-17:00'}
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        audit = AuditLog.objects.latest('created_at')
        self.assertEqual(audit.action, 'UPDATE')
        self.assertIn('working_hours', audit.new_values)
    
    def test_immediate_change_notifies_office(self):
        """Applying immediate change should notify staff users."""
        initial_notification_count = Notification.objects.filter(
            recipient=self.staff_user
        ).count()
        
        PartnerUpdateService.apply_immediate_change(
            user=self.partner_user,
            establishment=self.establishment,
            field_name='is_open_status',
            old_value=True,
            new_value=False
        )
        
        # Staff should have received notification
        new_notifications = Notification.objects.filter(
            recipient=self.staff_user,
            notification_type='partner_field_update'
        )
        self.assertGreater(new_notifications.count(), initial_notification_count)


class AccessControlTestCase(TransactionTestCase):
    """Test that unapproved partners cannot access partner dashboard."""
    
    def setUp(self):
        from users.models import Role
        
        # Get or create Partner role
        self.partner_role, _ = Role.objects.get_or_create(name='Partner')
        
        # Unapproved partner
        self.unapproved_user = User.objects.create_user(
            username='unapproved_partner',
            email='unapproved@test.com',
            password='testpass123'
        )
        self.unapproved_user.role = self.partner_role
        self.unapproved_user.account_status = 'active'
        self.unapproved_user.save()
        PartnerProfile.objects.create(
            user=self.unapproved_user,
            is_approved=False,
            status='pending'
        )
        
        # Approved partner
        self.approved_user = User.objects.create_user(
            username='approved_partner',
            email='approved@test.com',
            password='testpass123'
        )
        self.approved_user.role = self.partner_role
        self.approved_user.account_status = 'active'
        self.approved_user.save()
        PartnerProfile.objects.create(
            user=self.approved_user,
            is_approved=True,
            status='approved'
        )
        
        self.client = Client()
    
    def test_unapproved_partner_cannot_access_dashboard(self):
        """Unapproved partner should be redirected from partner dashboard."""
        # Use force_login to bypass axes requirements
        self.client.force_login(self.unapproved_user)
        
        response = self.client.get(reverse('partner_dashboard'))
        
        # Should redirect (302) or forbidden (403)
        self.assertIn(response.status_code, [302, 403])
    
    def test_approved_partner_can_access_dashboard(self):
        """Approved partner should be able to access partner dashboard."""
        # Use force_login to bypass axes requirements
        self.client.force_login(self.approved_user)
        
        response = self.client.get(reverse('partner_dashboard'))
        
        # Should be successful (200)
        self.assertEqual(response.status_code, 200)


class AdminPendingChangeViewTestCase(TransactionTestCase):
    """Test admin views for pending changes."""
    
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_view_test',
            email='admin_view@test.com',
            password='adminpass123'
        )
        
        self.partner_user = User.objects.create_user(
            username='partner_view',
            email='partner_view@test.com',
            password='partnerpass123'
        )
        PartnerProfile.objects.create(
            user=self.partner_user,
            is_approved=True
        )
        
        self.category = Category.objects.create(name='Admin View Test Category')
        self.establishment = Establishment.objects.create(
            name='Admin View Test Establishment',
            category=self.category,
            owner=self.partner_user,
            license_status='Approved',
            is_active=True
        )
        
        # Create a pending change
        self.pending_change = PendingChange.objects.create(
            establishment=self.establishment,
            field_name='name',
            old_value='Admin View Test Establishment',
            new_value='New Admin View Name',
            requested_by=self.partner_user
        )
        
        self.client = Client()
    
    def test_admin_can_view_pending_changes_list(self):
        """Admin should be able to view pending changes list."""
        self.client.force_login(self.admin_user)
        
        response = self.client.get(reverse('admin_pending_changes'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Admin View Name')
    
    @patch('management.services.pending_change_service.PendingChangeService._notify_partner_of_decision')
    def test_admin_can_approve_change(self, mock_notify):
        """Admin should be able to approve a pending change."""
        self.client.force_login(self.admin_user)
        
        response = self.client.post(
            reverse('admin_pending_change_action', kwargs={'pk': self.pending_change.pk}),
            {'action': 'approve'}
        )
        
        # Should redirect after action
        self.assertEqual(response.status_code, 302)
        
        # Refresh and check
        self.pending_change.refresh_from_db()
        self.assertEqual(self.pending_change.status, 'approved')
        
        self.establishment.refresh_from_db()
        self.assertEqual(self.establishment.name, 'New Admin View Name')
    
    def test_non_admin_cannot_view_pending_changes(self):
        """Non-admin user should not be able to access pending changes."""
        self.client.force_login(self.partner_user)
        
        response = self.client.get(reverse('admin_pending_changes'))
        
        # Should redirect or forbidden
        self.assertIn(response.status_code, [302, 403])


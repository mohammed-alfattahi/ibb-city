"""
Tests for Multi-Contact System
اختبارات نظام جهات الاتصال المتعدد

Tests covers:
1. EstablishmentContact model validation (Yemen phones, carriers)
2. ContactService CRUD operations and audit logging
3. Public visibility filtering
4. Ordering
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from unittest.mock import patch
from places.models import Establishment, EstablishmentContact, Category
from places.services.contact_service import ContactService
from management.models import AuditLog
from users.models import Role

User = get_user_model()


class EstablishmentContactTests(TestCase):
    def setUp(self):
        # Patch notifications to prevent async DB locks
        self.notify_patcher = patch('interactions.notifications.admin.AdminNotifications.notify_establishment_contact_updated')
        self.mock_notify = self.notify_patcher.start()
        
        # Patch the core notification service to stop all async threads
        self.service_patcher = patch('interactions.notifications.notification_service.NotificationService._process_event_sync')
        self.mock_service = self.service_patcher.start()
        
        self.addCleanup(self.notify_patcher.stop)
        self.addCleanup(self.service_patcher.stop)

        # Create Role
        self.partner_role, _ = Role.objects.get_or_create(name='Partner')

        # Create users
        self.partner_user = User.objects.create_user(
            username='partner', email='partner@ibbb.com', password='password',
            role=self.partner_role, account_status='active'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@ibbb.com', password='password'
        )
        
        # Create establishment
        self.category = Category.objects.create(name='Hotel')
        self.establishment = Establishment.objects.create(
            name='Test Hotel',
            owner=self.partner_user,
            category=self.category,
            approval_status='approved',
            is_active=True
        )

    def test_yemen_phone_validation(self):
        """Test validation logic for Yemen phone numbers."""
        # Valid cases
        valid_phones = [
            '777123456',
            '+967777123456',
            '04400000',
            '+9671123456'
        ]
        for phone in valid_phones:
            contact = EstablishmentContact(
                establishment=self.establishment,
                type='phone',
                carrier='sabafon',
                value=phone
            )
            contact.clean()  # Should not raise
            
        # Invalid cases
        invalid_phones = [
            '123',
            'notaphonenumber',
            '555123456', # Invalid start digit for mobile
        ]
        for phone in invalid_phones:
            contact = EstablishmentContact(
                establishment=self.establishment,
                type='phone',
                carrier='sabafon',
                value=phone
            )
            with self.assertRaises(ValidationError):
                contact.clean()

    def test_carrier_required_for_phone(self):
        """Test that carrier is required when type is phone."""
        contact = EstablishmentContact(
            establishment=self.establishment,
            type='phone',
            value='777123456'
        )
        with self.assertRaises(ValidationError):
            contact.clean()

    def test_add_multiple_contacts(self):
        """Test adding multiple contacts via service."""
        # Add Phone
        contact1, success, msg = ContactService.add_contact(
            user=self.partner_user,
            establishment=self.establishment,
            data={
                'type': 'phone',
                'carrier': 'sabafon',
                'value': '777123456',
                'label': 'Main'
            }
        )
        self.assertTrue(success)
        self.assertEqual(contact1.display_order, 1)
        
        # Add WhatsApp
        contact2, success, msg = ContactService.add_contact(
            user=self.partner_user,
            establishment=self.establishment,
            data={
                'type': 'whatsapp',
                'value': '777654321'
            }
        )
        self.assertTrue(success)
        self.assertEqual(contact2.display_order, 2)
        
        # Verify both exist
        self.assertEqual(self.establishment.contacts.count(), 2)

    def test_primary_contact_enforcement(self):
        """Test that setting a new primary contact unsets previous ones."""
        # First primary
        c1 = EstablishmentContact.objects.create(
            establishment=self.establishment, type='phone',carrier='you',
            value='733000000', is_primary=True
        )
        
        # Second primary
        c2 = EstablishmentContact.objects.create(
            establishment=self.establishment, type='phone', carrier='you',
            value='733111111', is_primary=True
        )
        
        c1.refresh_from_db()
        self.assertFalse(c1.is_primary)
        self.assertTrue(c2.is_primary)

    def test_tourist_visibility_groups(self):
        """Test grouping and visibility filtering for tourist view."""
        # Visible Phone
        EstablishmentContact.objects.create(
            establishment=self.establishment, type='phone', carrier='sabafon',
            value='711111111', is_visible=True, display_order=1
        )
        # Hidden Phone
        EstablishmentContact.objects.create(
            establishment=self.establishment, type='phone', carrier='you',
            value='733333333', is_visible=False, display_order=2
        )
        # Visible Facebook
        EstablishmentContact.objects.create(
            establishment=self.establishment, type='facebook',
            value='http://fb.com/test', is_visible=True, display_order=3
        )
        
        groups = ContactService.get_visible_contacts(self.establishment)
        
        self.assertEqual(len(groups['phones']), 1)
        self.assertEqual(groups['phones'][0].value, '711111111')
        self.assertEqual(len(groups['social']), 1)
        
    def test_audit_logging(self):
        """Test that modifications create audit logs."""
        # Add
        ContactService.add_contact(
            user=self.partner_user,
            establishment=self.establishment,
            data={'type': 'website', 'value': 'http://test.com'}
        )
        
        self.assertTrue(AuditLog.objects.filter(
            action='contact_added', 
            user=self.partner_user
        ).exists())

    def test_ordering(self):
        """Test reordering contacts."""
        c1 = EstablishmentContact.objects.create(
            establishment=self.establishment, type='other', value='1', display_order=1
        )
        c2 = EstablishmentContact.objects.create(
            establishment=self.establishment, type='other', value='2', display_order=2
        )
        
        # Swap order
        success, msg = ContactService.reorder_contacts(
            user=self.partner_user,
            establishment=self.establishment,
            ordered_ids=[str(c2.id), str(c1.id)]
        )
        
        self.assertTrue(success)
        c1.refresh_from_db()
        c2.refresh_from_db()
        
        self.assertEqual(c2.display_order, 0)
        self.assertEqual(c1.display_order, 1)

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from places.models import Establishment, Category
from management.models import Request, AuditLog
from unittest.mock import patch

User = get_user_model()

class PartnerEstablishmentUpdateViewTests(TestCase):
    def setUp(self):
        # Patch NotificationService to prevent async thread DB locks
        self.patcher = patch('interactions.notifications.notification_service.NotificationService.emit_event')
        self.mock_emit = self.patcher.start()
        
        # Create User
        self.password = 'password123'
        self.user = User.objects.create_user(username='partner_test', password=self.password)
        
        # Create Establishment
        self.category = Category.objects.create(name="Hotels")
        self.establishment = Establishment.objects.create(
            name="Original Name",
            owner=self.user,
            category=self.category,
            description="Original Description",
            latitude=10.0,
            longitude=20.0,
            contact_info={"phone": "123"},
            is_active=True
        )
        
        self.client = Client()
        self.client.force_login(self.user)
        self.url = reverse('establishment_update', args=[self.establishment.pk])

    def tearDown(self):
        self.patcher.stop()

    def test_update_non_sensitive_field(self):
        """
        Verify that updating non-sensitive fields (like opening_hours_text) 
        applies immediately and creates an AuditLog.
        """
        # Ensure we send minimal required fields plus the one we want to change
        data = {
            'name': 'Original Name',
            'description': 'Original Description',
            'category': self.category.id,
            'latitude': 10.0,
            'longitude': 20.0,
            'operational_status': 'active', # Required field
            'opening_hours_text': '9 AM - 5 PM', 
            # Note: If the form validation requires other fields, they must be included.
            # Assuming models are created with defaults or null=True where possible.
        }
        
        response = self.client.post(self.url, data)
        
        if response.status_code != 302:
            print(f"Form Errors (Non-Sensitive Test): {response.context['form'].errors}")
            
        self.assertEqual(response.status_code, 302) # Redirects on success

        # Refresh from DB
        self.establishment.refresh_from_db()
        self.assertEqual(self.establishment.opening_hours_text, '9 AM - 5 PM')
        
        # Verify Audit Log
        log = AuditLog.objects.filter(action='UPDATE', record_id=str(self.establishment.pk)).last()
        self.assertIsNotNone(log)
        self.assertIn('opening_hours_text', log.new_values)

    def test_update_sensitive_field(self):
        """
        Verify that updating a sensitive field (like name) 
        creates a Request, notifies admin, and does NOT update the Establishment immediately.
        """
        data = {
            'name': 'New Sensitive Name', # CHANGED (Sensitive)
            'description': 'Original Description',
            'category': self.category.id,
            'latitude': 10.0,
            'longitude': 20.0,
            'operational_status': 'active', # Required field
            'is_active': True,
            'is_open_status': True,
        }
        
        response = self.client.post(self.url, data)
        
        if response.status_code != 302:
            print(f"Form Errors (Sensitive Test): {response.context['form'].errors}")
            
        self.assertEqual(response.status_code, 302)

        # Refresh from DB - Should NOT change yet
        self.establishment.refresh_from_db()
        self.assertNotEqual(self.establishment.name, 'New Sensitive Name')
        self.assertEqual(self.establishment.name, 'Original Name')
        
        # Verify Request created
        req = Request.objects.filter(user=self.user, target_object_id=self.establishment.pk).last()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, 'PENDING')
        
        # Check logic for 'name' in changes. 
        # Request.changes depends on how RequestManager stores it.
        # It's usually a JSONField.
        changes = req.changes
        if isinstance(changes, str):
            import json
            changes = json.loads(changes)
            
        self.assertIn('name', changes)
        
        # Verify Notification call
        self.mock_emit.assert_called()
        # emit_event is called with keyword arguments, so check kwargs
        _, kwargs = self.mock_emit.call_args
        self.assertEqual(kwargs.get('event_name'), 'REQUEST_UPDATE')

    def test_update_mixed_fields(self):
        """
        Verify that mixed updates (sensitive + non-sensitive) 
        save non-sensitive changes immediately but create a request for sensitive ones.
        """
        data = {
            'name': 'Mixed Sensitive Name',   # Sensitive Change
            'description': 'Original Description',
            'category': self.category.id,
            'latitude': 10.0,
            'longitude': 20.0,
            'operational_status': 'active',
            'is_active': True,
            'is_open_status': True,
            'opening_hours_text': 'New Hours', # Non-Sensitive Change
        }
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        # Refresh from DB
        self.establishment.refresh_from_db()
        
        # Non-sensitive should be updated
        self.assertEqual(self.establishment.opening_hours_text, 'New Hours')
        
        # Sensitive should NOT be updated
        self.assertNotEqual(self.establishment.name, 'Mixed Sensitive Name')
        self.assertEqual(self.establishment.name, 'Original Name')
        
        # Verify Request created
        req = Request.objects.filter(user=self.user, target_object_id=self.establishment.pk).last()
        self.assertIsNotNone(req)
        self.assertIn('name', req.changes if isinstance(req.changes, dict) else str(req.changes))

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from places.models import Establishment, Category
from places.services.open_status_service import OpenStatusService
from management.models import AuditLog
from unittest.mock import patch, MagicMock

User = get_user_model()

from users.models import Role

from django.test import TestCase, override_settings

@override_settings(LANGUAGE_CODE='en-us')
class OpenStatusSystemTest(TestCase):
    def setUp(self):
        # Create Role
        self.role = Role.objects.create(name='Partner')
        # Create Users
        self.owner = User.objects.create_user(username='owner', password='password', role=self.role)
        self.other_user = User.objects.create_user(username='other', password='password', role=self.role)
        
        # Create Category
        self.category = Category.objects.create(name='Hotel')
        
        # Create Establishment
        self.establishment = Establishment.objects.create(
            name='My Hotel',
            owner=self.owner,
            category=self.category,
            is_open_now=True
            # Other fields use defaults
        )
        
        # Mock Notification Service patcher
        self.notify_patcher = patch('places.services.open_status_service.NotificationService.emit_event')
        self.mock_notify = self.notify_patcher.start()

    def tearDown(self):
        self.notify_patcher.stop()

    def test_service_toggle_success(self):
        """Owner can toggle status via service."""
        success, msg = OpenStatusService.toggle_open_status(self.owner, self.establishment, False)
        
        self.assertTrue(success)
        self.establishment.refresh_from_db()
        self.assertFalse(self.establishment.is_open_now)
        self.assertEqual(self.establishment.open_status_updated_by, self.owner)
        
        # Check Audit Log
        log = AuditLog.objects.last()
        self.assertEqual(log.action, 'UPDATE_OPEN_STATUS')
        self.assertEqual(str(log.record_id), str(self.establishment.id))
        self.assertEqual(log.diff['is_open_now']['old'], 'Open')
        self.assertEqual(log.diff['is_open_now']['new'], 'Closed')
        
        # Check Notification
        self.mock_notify.assert_called_with(
            'OPEN_STATUS_CHANGED',
            {'place_name': 'My Hotel', 'status': 'Closed', 'user': 'owner'},
            {'role': 'staff'},
            priority='medium'
        )

    def test_service_permission_denied(self):
        """Non-owner cannot toggle."""
        success, msg = OpenStatusService.toggle_open_status(self.other_user, self.establishment, False)
        self.assertFalse(success)
        self.establishment.refresh_from_db()
        self.assertTrue(self.establishment.is_open_now) # Unchanged

    def test_view_toggle_success(self):
        """Owner can toggle via view."""
        self.client.force_login(self.owner)
        url = reverse('toggle_establishment_status', kwargs={'pk': self.establishment.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_open']) # Toggled to False
        
        self.establishment.refresh_from_db()
        self.assertFalse(self.establishment.is_open_now)

    def test_view_permission_denied(self):
        """Other user gets 403."""
        self.client.force_login(self.other_user)
        url = reverse('toggle_establishment_status', kwargs={'pk': self.establishment.pk})
        response = self.client.post(url)
        
        # View raises PermissionDenied which might render 403.
        # Check status code
        self.assertEqual(response.status_code, 403)

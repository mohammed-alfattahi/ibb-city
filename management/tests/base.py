from django.test import TestCase
from django.contrib.auth import get_user_model
from interactions.notifications.notification_service import NotificationService
from unittest.mock import patch

User = get_user_model()

class BaseTestCase(TestCase):
    """
    Base test class with common setup helpers.
    """
    
    def setUp(self):
        # Create standard users
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.partner = User.objects.create_user('partner', 'partner@example.com', 'password')
        self.tourist = User.objects.create_user('tourist', 'tourist@example.com', 'password')
        
    def create_request(self, user, req_type='ADD_PLACE'):
        from management.models import Request
        return Request.objects.create(
            user=user,
            request_type=req_type,
            status='PENDING',
            description="Test Request"
        )
    
    def assertNotificationSent(self, mock_notify, count=1):
        """Helper to check if notification service was called."""
        self.assertEqual(mock_notify.call_count, count)

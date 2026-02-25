"""
Tests for Notification Outbox System
"""
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from interactions.notifications.outbox import NotificationOutbox
from interactions.notifications.notification_service import NotificationService
from interactions.notifications.providers.base import ProviderError, SendResult

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class OutboxModelTest(TestCase):
    """Test NotificationOutbox model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_outbox_entry(self):
        """Test creating an outbox entry."""
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            channel='push',
            provider='fcm',
            title='Test Title',
            body='Test Body',
            payload={'key': 'value'}
        )
        
        self.assertEqual(outbox.status, 'queued')
        self.assertEqual(outbox.attempts, 0)
        self.assertIsNone(outbox.sent_at)
    
    def test_mark_sent(self):
        """Test marking notification as sent."""
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            title='Test',
            body='Test'
        )
        
        outbox.mark_sent()
        
        self.assertEqual(outbox.status, 'sent')
        self.assertIsNotNone(outbox.sent_at)
    
    def test_mark_failed_with_retry(self):
        """Test marking as failed increments attempts."""
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            title='Test',
            body='Test'
        )
        
        outbox.mark_failed("Connection error")
        
        self.assertEqual(outbox.status, 'retrying')
        self.assertEqual(outbox.attempts, 1)
        self.assertEqual(outbox.last_error, "Connection error")
    
    def test_mark_dead_after_max_attempts(self):
        """Test that status becomes 'dead' after max attempts."""
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            title='Test',
            body='Test',
            attempts=4,  # One less than max (5)
            max_attempts=5
        )
        
        outbox.mark_failed("Final error")
        
        self.assertEqual(outbox.status, 'dead')
        self.assertEqual(outbox.attempts, 5)
    
    def test_retry_countdown_exponential(self):
        """Test exponential backoff calculation."""
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            title='Test',
            body='Test'
        )
        
        # First retry: 2^0 * 30 = 30s
        outbox.attempts = 0
        self.assertEqual(outbox.retry_countdown, 30)
        
        # Second retry: 2^1 * 30 = 60s
        outbox.attempts = 1
        self.assertEqual(outbox.retry_countdown, 60)
        
        # Fifth retry: 2^4 * 30 = 480s
        outbox.attempts = 4
        self.assertEqual(outbox.retry_countdown, 480)
        
        # Max cap at 1 hour
        outbox.attempts = 10
        self.assertEqual(outbox.retry_countdown, 3600)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class NotificationServiceTest(TestCase):
    """Test NotificationService with outbox pattern."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='partner',
            email='partner@example.com',
            password='testpass123'
        )
    
    @patch('interactions.tasks.notifications.send_outbox_notification.delay')
    def test_enqueue_notification_creates_outbox(self, mock_delay):
        """Test that enqueue_notification creates outbox entry."""
        outbox = NotificationService.enqueue_notification(
            recipient=self.user,
            title='Test Notification',
            body='This is a test',
            channel='push',
            provider='fcm'
        )
        
        self.assertIsNotNone(outbox)
        self.assertEqual(outbox.recipient, self.user)
        self.assertEqual(outbox.status, 'queued')
        # Note: mock_delay assertion would require TransactionTestCase


class CeleryTaskTest(TransactionTestCase):
    """Test Celery tasks for notification delivery."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='celeryuser',
            email='celery@example.com',
            password='testpass123'
        )
    
    @patch('interactions.notifications.providers.fcm.FCMProvider.send_to_user')
    def test_task_marks_sent_on_success(self, mock_send):
        """Test that task marks outbox as sent on success."""
        from interactions.tasks.notifications import send_outbox_notification
        
        mock_send.return_value = SendResult(success=True, message_id='msg123')
        
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            channel='push',
            provider='fcm',
            title='Test',
            body='Test body'
        )
        
        # Run task synchronously
        send_outbox_notification(str(outbox.id))
        
        outbox.refresh_from_db()
        self.assertEqual(outbox.status, 'sent')
        self.assertIsNotNone(outbox.sent_at)
    
    @patch('interactions.notifications.providers.fcm.FCMProvider.send_to_user')
    def test_task_marks_failed_on_error(self, mock_send):
        """Test that task marks outbox as retrying on error."""
        from interactions.tasks.notifications import send_outbox_notification
        
        mock_send.side_effect = ProviderError("Connection failed", "fcm", retriable=True)
        
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            channel='push',
            provider='fcm',
            title='Test',
            body='Test body'
        )
        
        # Run task - will raise for retry but we catch it
        try:
            send_outbox_notification(str(outbox.id))
        except Exception:
            pass
        
        outbox.refresh_from_db()
        self.assertIn(outbox.status, ['retrying', 'failed'])
        self.assertEqual(outbox.attempts, 1)
    
    def test_task_idempotent_on_already_sent(self):
        """Test that task does nothing if already sent."""
        from interactions.tasks.notifications import send_outbox_notification
        
        outbox = NotificationOutbox.objects.create(
            recipient=self.user,
            channel='push',
            provider='fcm',
            title='Test',
            body='Test body',
            status='sent'
        )
        
        # Should return early without error
        send_outbox_notification(str(outbox.id))
        
        outbox.refresh_from_db()
        self.assertEqual(outbox.status, 'sent')

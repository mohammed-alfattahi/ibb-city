"""
Acceptance tests for the notification system.
Covers: partner decision notifications, weather alerts,
notification list page, unread count, mark-read, and type filter.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from interactions.models import Notification
from interactions.notifications.notification_service import NotificationService
from users.models import PartnerProfile, Role

User = get_user_model()


class NotificationTestMixin:
    """Shared setup for notification tests."""

    @classmethod
    def setUpTestData(cls):
        # Create roles
        cls.tourist_role, _ = Role.objects.get_or_create(name='Tourist')
        cls.partner_role, _ = Role.objects.get_or_create(name='Partner')
        cls.staff_role, _ = Role.objects.get_or_create(name='Staff')

        # Create FeatureToggle for notifications
        from management.models import FeatureToggle
        FeatureToggle.objects.get_or_create(
            key='enable_notifications',
            defaults={'is_enabled': True}
        )

    def setUp(self):
        self.client = Client()
        # Staff user
        self.staff = User.objects.create_user(
            username='staff_test', email='staff@test.com',
            password='StaffPass123!', is_staff=True
        )
        # Partner user
        self.partner_user = User.objects.create_user(
            username='partner_test', email='partner@test.com',
            password='PartnerPass123!', role=self.partner_role
        )
        self.partner_profile = PartnerProfile.objects.create(
            user=self.partner_user,
            organization_name='Test Co',
            status='pending'
        )
        # Tourist user
        self.tourist = User.objects.create_user(
            username='tourist_test', email='tourist@test.com',
            password='TouristPass123!', role=self.tourist_role
        )


class PartnerNotificationTests(NotificationTestMixin, TestCase):
    """Tests 4,5,6: Partner decision notifications are correct."""

    def test_partner_approved_creates_notification(self):
        """Admin approves partner → partner sees partner_approved notification."""
        NotificationService.emit_event(
            'PARTNER_APPROVED',
            {'partner_name': self.partner_user.get_full_name()},
            {'user_id': self.partner_user.pk}
        )
        notif = Notification.objects.filter(
            recipient=self.partner_user,
            notification_type='partner_approved'
        )
        self.assertTrue(notif.exists(), "Partner should receive approval notification")
        self.assertIn('اعتماد', notif.first().title)

    def test_partner_rejected_creates_notification(self):
        """Admin rejects partner → partner sees partner_rejected with reason."""
        reason = 'وثائق غير مكتملة'
        NotificationService.emit_event(
            'PARTNER_REJECTED',
            {'partner_name': self.partner_user.get_full_name(), 'reason': reason},
            {'user_id': self.partner_user.pk}
        )
        notif = Notification.objects.filter(
            recipient=self.partner_user,
            notification_type='partner_rejected'
        )
        self.assertTrue(notif.exists(), "Partner should receive rejection notification")
        self.assertIn(reason, notif.first().message)

    def test_partner_needs_info_creates_notification(self):
        """Admin requests info → partner sees partner_needs_info notification."""
        info_msg = 'يرجى إرفاق السجل التجاري'
        NotificationService.emit_event(
            'PARTNER_NEEDS_INFO',
            {
                'partner_name': self.partner_user.get_full_name(),
                'info_message': info_msg,
            },
            {'user_id': self.partner_user.pk}
        )
        notif = Notification.objects.filter(
            recipient=self.partner_user,
            notification_type='partner_needs_info'
        )
        self.assertTrue(notif.exists(), "Partner should receive info-request notification")
        self.assertIn(info_msg, notif.first().message)

    def test_partner_notification_not_sent_to_others(self):
        """Partner notifications should NOT be sent to tourists."""
        NotificationService.emit_event(
            'PARTNER_APPROVED',
            {'partner_name': self.partner_user.get_full_name()},
            {'user_id': self.partner_user.pk}
        )
        tourist_notifs = Notification.objects.filter(recipient=self.tourist)
        # staff_notifs = Notification.objects.filter(recipient=self.staff)
        # Note: Staff might receive a copy depending on implementation, strictly checking tourist for now.
        self.assertEqual(tourist_notifs.count(), 0, "Tourist should not get partner notification")


class WeatherAlertNotificationTests(NotificationTestMixin, TestCase):
    """Test 28: Weather alert creates in-app notifications for all users."""

    def test_weather_alert_creates_notifications_for_all_users(self):
        """Creating a weather alert → all active users receive notification."""
        NotificationService.emit_event(
            'WEATHER_ALERT',
            {
                'title': '⚠️ تحذير أحمر - عاصفة رعدية',
                'message': 'يرجى توخي الحذر وتجنب الخروج.',
                'severity': 'RED',
            },
            {'role': 'all'},
            priority='high'
        )
        # All three users should get the notification
        for user in [self.staff, self.partner_user, self.tourist]:
            notifs = Notification.objects.filter(recipient=user, event_type='WEATHER_ALERT')
            self.assertTrue(
                notifs.exists(),
                f"User {user.username} should receive weather alert"
            )
            self.assertIn('عاصفة', notifs.first().title)

    def test_weather_alert_unread_count_increments(self):
        """After weather alert, unread count increases for each user."""
        before = Notification.objects.filter(recipient=self.tourist, is_read=False).count()
        NotificationService.emit_event(
            'WEATHER_ALERT',
            {'title': 'تنبيه', 'message': 'أمطار خفيفة'},
            {'role': 'all'}
        )
        after = Notification.objects.filter(recipient=self.tourist, is_read=False).count()
        self.assertEqual(after, before + 1, "Unread count should increase by 1")


class NotificationUITests(NotificationTestMixin, TestCase):
    """Tests for notification list page, mark-read, and type filter."""

    def _create_sample_notifications(self):
        """Create a mix of notifications for testing."""
        NotificationService.emit_event(
            'PARTNER_APPROVED',
            {'partner_name': 'Test'},
            {'user_id': self.partner_user.pk}
        )
        NotificationService.emit_event(
            'WEATHER_ALERT',
            {'title': 'تنبيه طقس', 'message': 'أمطار'},
            {'role': 'all'}
        )

    def test_notification_list_page_accessible(self):
        """Authenticated user can access /notifications/ page."""
        self.client.force_login(self.tourist)
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'مركز الإشعارات')

    def test_notification_list_shows_user_notifications(self):
        """User sees only their own notifications."""
        self._create_sample_notifications()
        self.client.force_login(self.partner_user)
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 200)
        # Partner should see both their partner approval + weather alert
        self.assertGreaterEqual(
            len(response.context['notifications']),
            2,
            "Partner should see at least 2 notifications"
        )

    def test_mark_notification_read(self):
        """POST to mark-read sets is_read=True and read_at."""
        self._create_sample_notifications()
        self.client.force_login(self.partner_user)
        notif = Notification.objects.filter(recipient=self.partner_user, is_read=False).first()
        self.assertIsNotNone(notif)

        response = self.client.post(
            reverse('mark_notification_read', args=[notif.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read, "Notification should be marked as read")
        self.assertIsNotNone(notif.read_at, "read_at should be set")

    def test_type_filter_partner(self):
        """?type=partner shows only partner notifications."""
        self._create_sample_notifications()
        self.client.force_login(self.partner_user)
        response = self.client.get(reverse('notification_list') + '?type=partner')
        self.assertEqual(response.status_code, 200)
        for notif in response.context['notifications']:
            self.assertIn(notif.notification_type, [
                'partner_approved', 'partner_rejected', 'partner_needs_info'
            ], f"Filter should only show partner types, got {notif.notification_type}")

    def test_type_filter_weather(self):
        """?type=weather shows only weather alert notifications."""
        self._create_sample_notifications()
        self.client.force_login(self.tourist)
        response = self.client.get(reverse('notification_list') + '?type=weather')
        self.assertEqual(response.status_code, 200)
        for notif in response.context['notifications']:
            self.assertEqual(
                notif.event_type, 'WEATHER_ALERT',
                f"Filter should only show weather alerts, got {notif.event_type}"
            )

    def test_unread_count_api(self):
        """API endpoint returns correct unread count."""
        self._create_sample_notifications()
        self.client.force_login(self.tourist)
        response = self.client.get(reverse('unread_count'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertGreaterEqual(data['count'], 1, "Should have at least 1 unread notification")

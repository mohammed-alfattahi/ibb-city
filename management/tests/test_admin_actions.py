from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from places.models import Establishment, Category
from interactions.models import Report
from django.utils import timezone

User = get_user_model()

from django.test import TestCase, Client, override_settings

@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AdminActionsTest(TestCase):
    def setUp(self):
        # Create Admin User
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.client = Client()
        self.client.force_login(self.admin)
        
        # Create Regular User
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )
        
        # Create Establishment
        self.category = Category.objects.create(name='Test Category')
        self.establishment = Establishment.objects.create(
            name='Test Place',
            owner=self.user,
            category=self.category,
            approval_status='pending'
        )
        
        # Create Report
        self.report = Report.objects.create(
            user=self.user,
            content_object=self.establishment,
            report_type='SPAM',
            description='Test Report'
        )

    def test_establishment_approval(self):
        """Test P1-11: Establishment Approval Logic"""
        url = reverse('admin_establishment_approve', args=[self.establishment.pk])
        response = self.client.post(url, follow=True)
        
        self.establishment.refresh_from_db()
        self.assertEqual(self.establishment.approval_status, 'approved')
        self.assertTrue(self.establishment.approved_by == self.admin)
        self.assertContains(response, "تمت الموافقة")

    def test_establishment_rejection(self):
        """Test P1-11: Establishment Rejection Logic"""
        # Reset to pending
        self.establishment.approval_status = 'pending'
        self.establishment.save()
        
        url = reverse('admin_establishment_reject', args=[self.establishment.pk])
        response = self.client.post(url, {'reason': 'Invalid data'}, follow=True)
        
        self.establishment.refresh_from_db()
        self.assertEqual(self.establishment.approval_status, 'rejected')
        self.assertEqual(self.establishment.rejected_reason, 'Invalid data')
        self.assertContains(response, "تم رفض")

    def test_user_toggle(self):
        """Test P1-13: User Toggle Logic"""
        url = reverse('admin_user_toggle', args=[self.user.pk])
        
        # Deactivate
        response = self.client.post(url, follow=True)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertContains(response, "تم تعطيل")
        
        # Reactivate
        response = self.client.post(url, follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertContains(response, "تم تفعيل")

    def test_report_action(self):
        """Test P1-12: Report Action Logic"""
        url = reverse('admin_report_action', args=[self.report.pk])
        
        # Mark Reviewed (IN_PROGRESS)
        response = self.client.post(url, {'action': 'reviewed'}, follow=True)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'IN_PROGRESS')
        self.assertEqual(self.report.assigned_to, self.admin)
        
        # Mark Resolved
        response = self.client.post(url, {'action': 'resolve'}, follow=True)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'RESOLVED')
        # self.assertEqual(self.report.resolved_by, self.admin) # No resolved_by field
